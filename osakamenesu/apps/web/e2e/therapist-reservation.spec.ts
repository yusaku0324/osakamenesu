import { test, expect } from '@playwright/test'

/**
 * This spec verifies that therapist cards on the search page navigate to the
 * staff detail view and that the reservation form can be submitted (with the
 * network call mocked).
 */
test('therapist card navigates to staff page and reservation can be sent', async ({ page, baseURL }) => {
  await page.route('**/api/reservations', async (route) => {
    await route.fulfill({ status: 201, body: JSON.stringify({ id: 'e2e-reservation' }) })
  })

  await page.goto(`${baseURL}/search`)

  const therapistCard = page.getByTestId('therapist-card').first()
  await expect(therapistCard).toBeVisible()

  const staffLink = therapistCard.locator('a').first()
  const targetHref = await staffLink.getAttribute('href')
  await expect(targetHref).toContain('/profiles/')
  await expect(targetHref).toContain('/staff/')

  await staffLink.click()
  await expect(page).toHaveURL(/\/profiles\/.+\/staff\//)
  await expect(page.getByText('WEB予約リクエスト')).toBeVisible()

  await page.getByLabel('お名前 *').fill('E2E テスター')
  await page.getByLabel('お電話番号 *').fill('09012345678')
  await page.getByRole('button', { name: '予約リクエストを送信' }).click()

  await expect(page.getByText('送信が完了しました。店舗からの折り返しをお待ちください。')).toBeVisible()
})
