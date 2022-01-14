/*
    Sync MAL & Notion
*/
import { Client } from "@notionhq/client"
import axios from "axios"
import dotenv from "dotenv"
import chunk from "lodash"

// Config
dotenv.config()
const notion = new Client({ auth: process.env.NOTION_INTERNAL_INTEGRATION_TOKEN })
const databaseID = process.env.NOTION_DATABASE_ID
const malUsername = process.env.MAL_USERNAME
const OPERATION_BATCH_SIZE = 10

// Local Data Store
const myanimelistIDToNotionPageID = {}

function main() {
    // https://mathieularose.com/main-function-in-node-js
    // setInitialMyanimelistToNotionIDMap().then(syncNotionDatabaseWithMyanimelist)
    createNotionDatabase().then(() => console.log("Done creating."))
}

main()

async function createNotionDatabase() {
    const parentID = "f6b65ac3f59947d3a30ee0631d55e8d6"
    const response = await notion.pages.retrieve({ page_id: parentID })

    return notion.databases.create({
        parent: {
            type: "page_id",
            page_id: response.id,
        },
        title: [
            {
                type: "text",
                text: {
                    content: "MyAnimeList",
                    link: null,
                },
            },
        ],
        properties: {
            Title: {
                title: {},
            },
            Yes: {
                checkbox: {},
            },
        },
    })
}

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
    const baseURL = "https://api.jikan.moe/v3"

    let page = 1
    let animelist = []
    do {
        try {
            const res = await axios.get(`${baseURL}/user/${malUsername}/animelist/all/${page}`)
        } catch (err) {
            console.error(err)
        }

        const anime = await res.data.anime
        animelist.push(anime)
        page += 1
    } while (anime.length)

    return animelist
}

function getOperationsToSyncWithNotion(myanimelist) {
    const pagesToCreate = []
    const pagesToUpdate = []

    for (const anime of myanimelist) {
        const pageID = myanimelistIDToNotionPageID[anime.number]
        if (pageID) {
            pagesToUpdate.push({
                ...anime,
                pageID,
            })
        } else {
            pagesToCreate.push(anime)
        }
    }

    return {
        create: pagesToCreate,
        update: pagesToUpdate,
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

    return animelist.map((anime) => {
        return {
            pageID: anime.id,
            myanimelistID: anime.properties["MAL ID"].number,
        }
    })
}

// TODO
async function getPropertiesFromAnime(anime) {
    return {
        Name: {
            title: [{ type: "text", text: { content: anime.title } }],
        },
        URL: {
            url: anime.url,
        },
    }
}

async function createPages(pagesToCreate) {
    const pagesToCreateChunks = chunk(pagesToCreate, OPERATION_BATCH_SIZE)

    for (const pagesToCreateBatch of pagesToCreateChunks) {
        await Promise.all(
            pagesToCreateBatch.map((anime) =>
                notion.pages.create({
                    parent: { database_id: databaseID },
                    properties: getPropertiesFromAnime(anime),
                })
            )
        )
        console.log(`Completed batch size: ${pagesToCreateBatch.length}`)
    }
}

async function updatePages(pagesToUpdate) {
    const pagesToUpdateChunks = chunk(pagesToUpdate, OPERATION_BATCH_SIZE)

    for (const pagesToUpdateBatch of pagesToUpdateChunks) {
        await Promise.all(
            pagesToUpdateBatch.map(({ pageID, ...anime }) =>
                notion.pages.update({
                    page_id: pageID,
                    properties: getPropertiesFromAnime(anime),
                })
            )
        )
        console.log(`Completed batch size: ${pagesToUpdateBatch.length}`)
    }
}
