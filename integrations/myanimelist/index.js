/*
    Sync MAL & Notion
*/
import { Client } from "@notionhq/client"
import axios from "axios"
import dotenv from "dotenv"
import chunk from "lodash"
import fs from "fs"

import inquirer from "inquirer"
import InquirerFuzzyPath from "inquirer-fuzzy-path"
import ora from "ora"
import chalk from "chalk"

// Config
inquirer.registerPrompt("fuzzypath", InquirerFuzzyPath)
dotenv.config()

// Globals
let configFile = ""
let CFG = {}
const notion = new Client({ auth: process.env.NOTION_API_KEY })
const myanimelistIDToNotionPageID = {}

async function setInitialMyanimelistToNotionIDMap() {
    const currentAnimelist = await getAnimelistFromNotionDatabase()
    for (const { pageID, myanimelistID } of currentAnimelist) {
        myanimelistIDToNotionPageID[myanimelistID] = pageID
    }
}

async function syncNotionDatabaseWithMyanimelist() {
    const animelist = await getAnimelistFromMyanimelist()
    console.log(chalk.blue(`\nFetched ${animelist.length} anime from Notion.`))

    const { pagesToCreate, pagesToUpdate } = getOperationsToSyncWithNotion(animelist)

    console.log(chalk.white(`\n${pagesToCreate.length} new anime to add to Notion.`))
    await createPages(pagesToCreate)

    console.log(chalk.white(`\n${pagesToUpdate.length} anime to update in Notion.`))
    await updatePages(pagesToUpdate)

    console.log(chalk.green("\nNotion database synced with Myanimelist."))
}

async function getAnimelistFromMyanimelist() {
    const baseURL = "https://api.jikan.moe/v3"
    const malUsername = CFG.myanimelist.malUsername

    const animelist = []
    let page = 1
    let anime = {}
    do {
        let res = {}
        try {
            res = await axios.get(`${baseURL}/user/${malUsername}/animelist/all/${page}`)
        } catch (err) {
            console.error(err)
        }

        anime = await res.data.anime
        animelist.push(...anime)
        page += 1
    } while (anime.length && page < 8)

    return animelist
}

async function getAnimelistFromNotionDatabase() {
    const animelist = []
    let cursor = undefined

    do {
        const { results, nextCursor } = await notion.databases.query({
            database_id: CFG.myanimelist.databaseID,
            start_cursor: cursor,
        })
        animelist.push(...results)
        cursor = nextCursor
    } while (cursor)

    return animelist.map((anime) => {
        return {
            pageID: anime.id,
            myanimelistID: anime.properties["MAL ID"].number,
        }
    })
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

// TODO
async function getPropertiesFromAnime(anime) {
    return {
        Title: {
            // An array of rich text objects
            title: [{ type: "text", text: { content: anime.title } }],
        },
        Score: {
            number: anime.score,
        },
        "MAL ID": {
            number: anime.mal_id,
        },
        "MAL URL": {
            url: anime.url,
        },
        // "Is Rewatching?": {
        //     checkbox: anime.is_rewatching,
        // },
        // "Watch Start Date": {
        //     date: anime.watch_start_date,
        // },
        // "Watch End Date": {
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

async function main() {
    // Setup
    let spinner = {}
    let response = {}

    // Load config
    response = await inquirer.prompt([
        {
            type: "fuzzypath",
            name: "path",
            excludePath: (nodePath) => nodePath.startsWith("node_modules"),
            itemType: "file",
            message: "Select the config file to be loaded: ",
            suggestOnly: false,
            depthLimit: 5,
        },
    ])
    configFile = response.path
    CFG = JSON.parse(await fs.promises.readFile(configFile, "utf-8"))

    // Check Root Page
    spinner = ora("Checking root page").start()
    try {
        response = await notion.pages.retrieve({
            page_id: CFG.general.rootPageID,
        })
        spinner.stop()
        console.log(chalk.green(`Found root page at ${response.url}`))
    } catch (err) {
        console.error(`Could not obtain root page: ${err}`)
        process.exit()
    }

    // Create a new DB for MAL, if one is not specified in config.json
    if (CFG.myanimelist.databaseID === "") {
        response = await inquirer.prompt({
            type: "list",
            name: "createNew",
            message: "MAL DB ID doesn't exist in config.json. Create a new DB?",
            choices: ["Yes", "No"],
        })

        if (response.createNew === "No") {
            process.exit()
        }

        spinner = ora("Creating new database for MAL").start()
        response = await notion.databases
            .create({
                parent: {
                    type: "page_id",
                    page_id: CFG.general.rootPageID,
                },
                title: [{ type: "text", text: { content: "MyAnimeList" } }],
                properties: CFG.myanimelist.properties,
            })
            .then((res) => {
                spinner.stop()
                console.log(chalk.green("Created new database for MyAnimeList"))
                console.log(chalk.blue(`Live at ${res.url}`))

                CFG.myanimelist.databaseID = res.id
                fs.writeFile(configFile, JSON.stringify(CFG, null, "\t"), "utf-8", (err) => {
                    if (err) {
                        console.error(err)
                    } else {
                        console.log(chalk.blue("\nUpdated config file with the databaseID."))
                    }
                })
            })
            .catch((err) => {
                console.error(err)
                process.exit()
            })
    }

    // Check MAL DB
    spinner = ora("Checking MAL DB").start()
    try {
        response = await notion.databases.retrieve({
            database_id: CFG.myanimelist.databaseID,
        })
        spinner.stop()
        console.log(chalk.green(`Found MAL DB at ${response.url}`))
    } catch (err) {
        console.error(`Could not obtain MAL DB: ${err}`)
        process.exit()
    }

    // Update local data store
    spinner = ora("Sycing local data store with MAL").start()
    await setInitialMyanimelistToNotionIDMap()
    spinner.stop()

    // Sync
    spinner = ora("Syncing local data store with Notion").start()
    await syncNotionDatabaseWithMyanimelist()
    spinner.stop()
}

main()
