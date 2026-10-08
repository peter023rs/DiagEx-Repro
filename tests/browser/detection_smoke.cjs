const assert = require("node:assert/strict");
const { chromium } = require("playwright");
(async () => {
  const browser = await chromium.launch({executablePath:process.env.CHROME_PATH, headless:true});
  const page = await browser.newPage({viewport:{width:1440,height:1050}});
  const errors = [], posts = [];
  let catalogUnavailable = false;
  await page.route("https://openrouter.ai/api/v1/models", route => {
    assert(!route.request().headers().authorization, "Public model list must not receive an API key");
    return route.fulfill({status:catalogUnavailable ? 503 : 200, contentType:"application/json", body:JSON.stringify({data:[
      {id:"test/vision", name:"Test Vision", architecture:{input_modalities:["image","text"]}, supported_parameters:["tools"]},
      {id:"test/reinspection", name:"Test Reinspection", architecture:{input_modalities:["image","text"]}, supported_parameters:["tools"]},
      {id:"test/text-only", architecture:{input_modalities:["text"]}, supported_parameters:["tools"]},
      {id:"test/no-tools", architecture:{input_modalities:["image"]}, supported_parameters:[]},
    ]})});
  });
  page.on("pageerror", error => errors.push(String(error)));
  page.on("request", request => { if (request.method() === "POST") posts.push(request.url()); });
  try {
    await page.goto(process.argv[2]);
    await page.locator("#serverStatus.online").waitFor();
    assert.equal(await page.locator("#modelPolicy").inputValue(), "glm");
    for (const [preset, model] of Object.entries({
      mimo:"xiaomi/mimo-v2.6-pro", glm:"z-ai/glm-5.3-flash",
      kimi:"moonshotai/kimi-k3", qwen_vl:"qwen/qwen3-vl-235b-a22b-instruct",
    })) {
      await page.locator("#modelPolicy").selectOption(preset);
      assert.equal(await page.locator("#visionModel").inputValue(), model);
      assert.equal(await page.locator("#reasoningModel").inputValue(), "");
      assert.equal(await page.locator("#provider").inputValue(), "openrouter");
    }
    assert(!(await page.locator("#visionModel").isDisabled()), "Model must be editable without finding a custom preset");
    await page.locator("#toggleKey").click();
    assert.equal(await page.locator("#apiKey").getAttribute("type"), "text");
    await page.locator("#toggleKey").click();
    await page.locator("#modelPolicy").selectOption("evaluation");
    await page.locator("#provider").selectOption("kimi");
    assert(await page.locator("#openrouterRouting").isHidden());
    assert(!(await page.locator("#visionModel").isDisabled()));
    await page.locator("#modelPolicy").selectOption("deepseek-flash");
    await page.waitForFunction(() => document.querySelectorAll("#modelSuggestions option").length === 2);
    assert.deepEqual(await page.locator("#modelSuggestions option").evaluateAll(nodes => nodes.map(n => n.value)), ["test/reinspection", "test/vision"]);
    await page.locator("#visionModel").fill("test/manual-model-id");
    assert.equal(await page.locator("#modelPolicy").inputValue(), "evaluation");
    assert.equal(await page.locator("#reasoningModel").inputValue(), "");
    catalogUnavailable = true;
    await page.locator("#refreshModels").click();
    await page.waitForFunction(() => document.querySelector("#modelCatalogStatus").textContent.includes("unavailable"));
    assert.equal(await page.locator("#visionModel").inputValue(), "test/manual-model-id");
    catalogUnavailable = false;
    await page.locator("#refreshModels").click();
    await page.waitForFunction(() => document.querySelector("#modelCatalogStatus").textContent.startsWith("2 models"));
    await page.locator("#visionModel").fill("test/vision");
    await page.locator("#reasoningModel").fill("test/reinspection");
    await page.locator("#openrouterRouting summary").click();
    await page.locator("#providerOrder").fill("xiaomi");
    await page.locator("#providerIgnore").fill("deepinfra");
    await page.locator("#providerFallbacks").selectOption("false");
    for (const language of ["zh-CN", "en"]) {
      await page.locator("#languageSwitch").selectOption(language);
      for (const width of [1440, 390]) {
        await page.setViewportSize({width,height:1050});
        assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `dashboard overflow at ${width}`);
      }
    }
    await page.setViewportSize({width:1440,height:1050});
    await page.evaluate(() => { window.scrollTo(0, 0); return new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))); });
    await page.screenshot({path:process.argv[3].replace("chinese-detection-results.png","dashboard.png"), fullPage:true});
    await page.locator("#fileInput").setInputFiles(process.argv[4]);
    await page.locator("#fileSummary:not(.hidden)").waitFor();
    await page.locator("#startButton").click();
    await page.locator("#resultSection:not(.hidden)").waitFor();
    await page.locator("#viewResultsButton").click();
    await page.locator("#items button").first().waitFor();
    assert.equal(await page.locator("#items button").count(), 2);
    await page.locator("#items button").last().click();
    assert.equal(await page.locator("#drawing rect.active").count(), 1);
    assert.equal(await page.locator("#inspector input, #inspector textarea, #inspector select").count(), 0);
    assert((await page.locator("#inspector").textContent()).includes("PT-002"));
    await page.locator("#layout").selectOption("side");
    await page.locator("#background").selectOption("dim");
    assert.equal(await page.locator("#drawing .source-layer").getAttribute("opacity"), "0.25");
    assert.equal(await page.locator("#sourceDrawing image").first().getAttribute("opacity"), null);
    await page.locator("#layout").selectOption("stacked");
    await page.locator("#layout").selectOption("overlay");
    await page.locator("#search").fill("V-001");
    assert.equal(await page.locator("#items button").count(), 1);
    assert.equal(await page.locator("#drawing rect.active").count(), 0);
    await page.locator("#search").fill("");
    await page.locator("#filter").selectOption("low");
    assert.equal(await page.locator("#items button").count(), 0);
    await page.locator("#filter").selectOption("all");
    await page.locator("#legendTab").click();
    for (const type of ["library", "text", "drawing"]) {
      await page.locator("#legendType").selectOption(type);
      assert.equal(await page.locator("#items button").count(), 1);
      await page.locator("#items button").click();
    }
    await page.locator("#candidateTab").click();
    await page.locator("#page").selectOption("1");
    assert.equal(await page.locator("#items button").count(), 2);
    await page.locator("#items button").first().click();
    assert(!(await page.locator("#inspector").textContent()).includes('"kind": "equipment"'));
    await page.locator("#symbolTab").click();
    await page.locator("#items button").last().click();
    await page.locator("#languageSwitch").selectOption("zh-CN");
    assert.equal(await page.locator("h1").textContent(), "符号检测结果");
    await page.locator("#zoomOut").click();
    await page.locator("#zoomIn").click();
    await page.locator("#fit").click();
    await page.locator("#focus").click();
    for (const id of ["toggleList", "toggleInspector"]) { await page.locator(`#${id}`).click(); await page.locator(`#${id}`).click(); }
    const download = page.waitForEvent("download");
    await page.locator("#downloadDetection").click();
    assert.equal((await download).suggestedFilename(), "detection.json");
    await page.locator("#reload").click();
    await page.locator("#items button").last().waitFor();
    await page.waitForTimeout(200);
    await page.screenshot({path:process.argv[3], fullPage:true});
    await page.locator("#layout").selectOption("side");
    await page.locator("#fit").click();
    await page.screenshot({path:process.argv[3].replace("chinese-detection-results.png","comparison.png"), fullPage:true});
    for (const width of [1440, 768, 390]) {
      await page.setViewportSize({width,height:900});
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `overflow at ${width}`);
    }
    assert.equal(posts.filter(url => url.includes("/api/extractions")).length, 1);
    assert(!posts.some(url => /review|graph/.test(url)));
    assert.deepEqual(errors, []);
    console.log("PASS: editable OpenRouter models, catalog and offline fallback, custom-model job, viewer, languages, filters, comparison, downloads, responsive layouts; no review requests");
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode=1; });
