// just downloads the *.json.gz and *.stock.json from Honza's gh-pages site
const fs = require('fs').promises;
const fsSync = require('fs');
const path = require('path');
const zlib = require("zlib"); 
const process = require('process');
const { execSync } = require('child_process');


const dataPath = ['web/build/data', 'web/public/data', '../web/public/data'].filter(f => fsSync.existsSync(f))[0];

const downloadBase = 'https://yaqwsx.github.io/jlcparts/data';

async function saveSource(filename) {
    //console.log(`Downloading ${`${downloadBase}/${filename}`}`);
    let resp = await fetch(`${downloadBase}/${filename}`);
    if (resp.ok) {
        let content = await resp.arrayBuffer();
        try {
            await fs.writeFile(`${dataPath}/${filename}`, new Uint8Array(Buffer.from(content)));
        } catch (x) {
            console.error(x);
        }
    }
}

fetch(`${downloadBase}/index.json`).then(async (resp) => {
    index = await resp.json();

    let sources = [];
    for (const cat in index.categories) {
        for (const subcat in index.categories[cat]) {
            sources.push(index.categories[cat][subcat].sourcename);
        }
    }

    const startTime = new Date().getTime();

    let promises = [];
    for (const source of sources) {
        promises.push(saveSource(`${source}.json.gz`));
        promises.push(saveSource(`${source}.stock.json`));
    }

    await Promise.all(promises);
    console.log(`Downloaded ${promises.length} files. Download took ${Math.round((new Date().getTime() - startTime) / 1000)} seconds`);
});

