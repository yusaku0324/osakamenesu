import { test, expect } from '@playwright/test'

test.describe('Gallery demo interactions', () => {
  test('dots and thumbnails navigate slides', async ({ page, baseURL }) => {
    await page.goto(`${baseURL}/demo/gallery`)

    const view = page.locator('[data-testid="gallery-view"]').first()
    await expect(view).toBeVisible()

    // Ensure we have multiple dots/thumbnails
    const dots = page.locator('[data-testid="gallery-dot"]')
    const thumbs = page.locator('[data-testid="gallery-thumb"]')
    await expect(dots).toHaveCount(5)
    await expect(thumbs).toHaveCount(5)

    // Helper to read scroll state
    const getState = async () => {
      return await view.evaluate((el) => ({
        left: (el as HTMLElement).scrollLeft,
        width: (el as HTMLElement).clientWidth,
      }))
    }

    // Click 2nd dot -> slide 2
    const s0 = await getState()
    await dots.nth(1).click()
    await expect.poll(async () => {
      const s = await getState()
      return Math.round(s.left)
    }).toBeGreaterThanOrEqual(Math.round(s0.width * 0.8))

    // Click 1st thumbnail -> back to slide 1
    await thumbs.first().click()
    await expect.poll(async () => {
      const s = await getState()
      return Math.round(s.left)
    }).toBeLessThanOrEqual(10)
  })

  test('drag swipe advances slide', async ({ page, baseURL }) => {
    await page.goto(`${baseURL}/demo/gallery`)
    const view = page.locator('[data-testid="gallery-view"]').first()
    await expect(view).toBeVisible()

    // Start from first slide
    await view.evaluate((el) => ((el as HTMLElement).scrollLeft = 0))
    const box = await view.boundingBox()
    if (!box) throw new Error('no bounding box')

    const y = box.y + box.height / 2
    const xStart = box.x + box.width * 0.75
    const xEnd = box.x + box.width * 0.25

    await page.mouse.move(xStart, y)
    await page.mouse.down()
    await page.mouse.move(xEnd, y, { steps: 8 })
    await page.mouse.up()

    // Expect to have moved near the width of one slide
    await expect.poll(async () => {
      const s = await view.evaluate((el) => ({
        left: (el as HTMLElement).scrollLeft,
        width: (el as HTMLElement).clientWidth,
      }))
      return Math.round((s as any).left)
    }).toBeGreaterThan(20)
  })
})
