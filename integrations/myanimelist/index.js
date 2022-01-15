/*
    Sync MAL & Notion
*/
import { Client } from "@notionhq/client"
import axios from "axios"
import dotenv from "dotenv"
import chunk from "lodash"
import fs from "fs"

// Config
dotenv.config()
const configFile = "./config.json"
const CFG = JSON.parse(await fs.promises.readFile(configFile, "utf-8"))

// Notion client
const notion = new Client({ auth: process.env.NOTION_API_KEY })

// Local Data Store
const myanimelistIDToNotionPageID = {}

function main() {
    // setInitialMyanimelistToNotionIDMap().then(syncNotionDatabaseWithMyanimelist)
    createNewNotionDatabase()
        .then((res) => {
            CFG.myanimelist.databaseID = res.id
            fs.writeFile(configFile, JSON.stringify(CFG, null, "\t"), "utf-8", (err) => {
                if (err) {
                    console.error(err)
                } else {
                    console.log("Updated config file with MAL databaseID.")
                }
            })
            console.log(`Created new database for MyAnimeList\nLive at ${res.url}`)
        })
        .catch((err) => {
            console.error(err)
        })

    testAddToNotionDatabase()
        .then((res) => console.log(`Updated: ${JSON.stringify(res, null, 2)}`))
        .catch((err) => console.error(`Error: ${err}`))
}

main()

async function createNewNotionDatabase() {
    const response = await notion.pages.retrieve({ page_id: CFG.general.rootPageID })

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
                type: "title",
                title: {},
            },
            Score: {
                type: "number",
                number: {},
            },
            "MAL ID": {
                type: "number",
                number: {},
            },
            "MAL URL": {
                type: "url",
                url: {},
            },
            "Is Rewatching?": {
                type: "checkbox",
                checkbox: {},
            },
            "Watch Start Date": {
                type: "date",
                date: {},
            },
            "Watch End Date": {
                type: "date",
                date: {},
            },
            Days: {
                type: "number",
                number: {
                    format: "number",
                },
            },
            "Watched Episodes": {
                type: "number",
                number: {
                    format: "number",
                },
            },
            Type: {
                type: "select",
                select: {},
            },
            Genres: {
                type: "multi_select",
                multi_select: {},
            },
        },
    })
}

async function testAddToNotionDatabase() {
    return notion.pages.create({
        parent: { database_id: CFG.myanimelist.databaseID },
        properties: {
            Title: {
                title: [{ type: "text", text: { content: "Test title" } }],
            },
            Score: {
                number: 10,
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

async function getPropertiesFromAnime(anime) {
    return {
        Title: {
            // An array of rich text objects
            title: [{ type: "text", text: { content: anime.title } }],
        },
        Score: {
            type: "number",
            number: anime.score,
        },
        "MAL ID": {
            type: "number",
            number: anime.mal_id,
        },
        "MAL URL": {
            type: "url",
            url: anime.url,
        },
        // "Is Rewatching?": {
        //     type: "checkbox",
        //     checkbox: anime.is_rewatching,
        // },
        // "Watch Start Date": {
        //     type: "date",
        //     date: anime.watch_start_date,
        // },
        // "Watch End Date": {
        //     type: "date",
        //     date: anime.watch_end_date,
        // },
    }
}

async function createPages(pagesToCreate) {
    const pagesToCreateChunks = chunk(pagesToCreate, CFG.general.opBatchSize)

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
    const pagesToUpdateChunks = chunk(pagesToUpdate, CFG.general.opBatchSize)

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
