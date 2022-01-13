/*
    Sync MAL & Notion
*/

const { Client } = require("@notionhq/client")
const dotenv = require("dotenv")
const fs = require("fs")

dotenv.config()
const notion = new Client({ auth: process.env.NOTION_CLIENT_ID })
const databaseID = process.env.NOTION_DATABASE_ID
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
    // https://stackoverflow.com/a/10011078
    const animelist = {};
    fs.readFile("animelist.json", "utf-8", (err, data) => {
        if (err) { throw err }
        animelist = JSON.parse(data)
    })
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