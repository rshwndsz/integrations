/*
    Sync MAL & Notion
*/

import Client from "@notionhq/client"
import axios from axios
import dotenv from "dotenv"
import { promises as fs } from "fs"

dotenv.config()
const notion = new Client({ auth: process.env.NOTION_CLIENT_ID })
const databaseID = process.env.NOTION_DATABASE_ID
const malUsername = process.env.MAL_USERNAME
const OPERATION_BATCH_SIZE = 10

// Local Data Store
const myanimelistIDToNotionPageID = {}
// Update local data store
setInitialMyanimelistToNotionIDMap().then(syncNotionDatabaseWithMyanimelist)


async function setInitialMyanimelistToNotionIDMap() {
    const currentAnimelist = await getAnimelistFromNotionDatabase()
    for (const { pageID, myanimelistID } of currentAnimelist) {
        myanimelistIDToNotionPageID[myanimelistID] = pageID
    }
}


async function syncNotionDatabaseWithMyanimelist() {
    const animelist = await getAnimelistFromMyanimelist()
    console.log(`Fetched ${animelist.length} anime from Notion.`)

    const { pagesToCreate, pagesToUpdate } = getOperationsToSyncWithNotion(animelist)

    console.log(`${pagesToCreate.length} new anime to add to Notion.`)
    await createPages(pagesToCreate)

    console.log(`${pagesToUpdate.length} anime to update in Notion.`)
    await updatePages(pagesToUpdate)

    console.log("Notion database synced with Myanimelist.")
}


async function getAnimelistFromMyanimelist() {
    const BASE_URL = "https://api.jikan.moe/v3"
    let page = 1
    let animelist = {}
    while (page < 3) {
        try {
            const res = await axios.get(
                `${BASE_URL}/user/${MAL_USERNAME}/animelist/all/${page}`
            )
            animelist = { ...res.data.anime }
        } catch (error) {
            console.error(error)
        }
        page += 1
    }
    await fs.writeFile("out.json", JSON.stringify(animelist))
}


function getOperationsToSyncWithNotion(myanimelist) {
    const pagesToCreate = []
    const pagesToUpdate = []

    for (const anime of myanimelist) {
        const pageID = myanimelistIDToNotionPageID[anime.number]
    }
}


async function getAnimelistFromNotionDatabase() {
    const animelist = []
    let cursor = undefined

    do {
        const { results, nextCursor } = await notion.databases.query({
            database_id: databaseID,
            start_cursor: cursor,
        })
        animelist.push(...results)
        cursor = nextCursor
    } while (cursor)
    console.log(`${animelist.length} anime fetched.`)

    return animelist.map(anime => {
        return {
            pageID: anime.id,
            myanimelistID: anime.properties["MAL ID"].number,
        }
    })
}