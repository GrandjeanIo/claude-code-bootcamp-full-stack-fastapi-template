import { type Browser, expect, type Page, test } from "@playwright/test"
import { createUser } from "./utils/privateApi"
import { randomEmail, randomItemTitle, randomPassword } from "./utils/random"
import { logInUser, logOutUser } from "./utils/user"

const steps = {
  firstItem: "Create your first item",
  nameEdited: "Edit your profile name",
  inviteSent: "Invite someone by email",
}

const step = (page: Page, name: string) =>
  page.getByRole("checkbox", { name, exact: true })

const checklist = (page: Page) =>
  page.getByRole("region", { name: "Get started" })

async function createItem(page: Page) {
  await page.goto("/items")
  await page.getByRole("button", { name: "Add Item" }).click()
  await page.getByLabel("Title").fill(randomItemTitle())
  await page.getByRole("button", { name: "Save" }).click()
  await expect(page.getByText("Item created successfully")).toBeVisible()
}

async function editName(page: Page) {
  await page.goto("/settings")
  await page.getByRole("tab", { name: "My profile" }).click()
  await page.getByRole("button", { name: "Edit" }).click()
  await page.getByLabel("Full name").fill("Onboarded User")
  await page.getByRole("button", { name: "Save" }).click()
  await expect(page.getByText("User updated successfully")).toBeVisible()
}

async function signUp(page: Page, email: string, password: string) {
  await page.goto("/signup")
  await page.getByTestId("full-name-input").fill("Test User")
  await page.getByTestId("email-input").fill(email)
  await page.getByTestId("password-input").fill(password)
  await page.getByTestId("confirm-password-input").fill(password)
  await page.getByRole("button", { name: "Sign Up" }).click()
  await expect(page).toHaveURL(/\/login$/)
}

async function invite(page: Page, email: string) {
  await page.getByLabel("Email to invite").fill(email)
  const response = page.waitForResponse("**/api/v1/onboarding/invite")
  await page.getByRole("button", { name: "Send invite" }).click()
  await response
}

test("User without onboarding record sees no checklist", async ({ page }) => {
  await page.goto("/")
  await expect(
    page.getByText("Welcome back, nice to see you again!"),
  ).toBeVisible()
  await expect(checklist(page)).not.toBeVisible()
})

test.describe("Onboarding checklist", () => {
  test.use({ storageState: { cookies: [], origins: [] } })
  let email: string
  let password: string

  test.beforeEach(async ({ page }) => {
    email = randomEmail()
    password = randomPassword()
    await signUp(page, email, password)
    await logInUser(page, email, password)
  })

  test("New user sees all steps unchecked", async ({ page }) => {
    await expect(checklist(page)).toBeVisible()
    for (const name of Object.values(steps)) {
      await expect(step(page, name)).not.toBeChecked()
    }
  })

  test("Item and name steps show as done and persist across login", async ({
    page,
  }) => {
    await createItem(page)
    await editName(page)
    await page.goto("/")

    await expect(step(page, steps.firstItem)).toBeChecked()
    await expect(step(page, steps.nameEdited)).toBeChecked()
    await expect(step(page, steps.inviteSent)).not.toBeChecked()

    await logOutUser(page)
    await logInUser(page, email, password)

    await expect(step(page, steps.firstItem)).toBeChecked()
    await expect(step(page, steps.nameEdited)).toBeChecked()
    await expect(step(page, steps.inviteSent)).not.toBeChecked()
  })

  test("Invite form shows success and marks the step done", async ({
    page,
  }) => {
    await invite(page, randomEmail())

    await expect(page.getByText("Invitation sent")).toBeVisible()
    await expect(step(page, steps.inviteSent)).toBeChecked()
  })

  test("Invite form shows a server error", async ({ page }) => {
    await invite(page, email)

    await expect(page.getByText("You cannot invite yourself")).toBeVisible()
    await expect(step(page, steps.inviteSent)).not.toBeChecked()
  })

  test("Invite form shows the invite limit error", async ({ page }) => {
    for (let i = 0; i < 5; i++) {
      await invite(page, randomEmail())
      await expect(step(page, steps.inviteSent)).toBeChecked()
    }
    await invite(page, randomEmail())

    await expect(page.getByText("Invitation limit reached")).toBeVisible()
  })

  test("Checklist is hidden once all steps are done", async ({ page }) => {
    await createItem(page)
    await editName(page)
    await page.goto("/")
    await invite(page, randomEmail())
    await expect(page.getByText("Invitation sent")).toBeVisible()

    await page.reload()
    await expect(
      page.getByText("Welcome back, nice to see you again!"),
    ).toBeVisible()
    await expect(checklist(page)).not.toBeVisible()
  })
})

const understatedNote = "The completion rate may be understated"

const localDate = (d: Date) =>
  `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`

const daysAgo = (days: number) => {
  const d = new Date()
  d.setDate(d.getDate() - days)
  return d
}

async function signUpInFreshContext(browser: Browser) {
  const context = await browser.newContext({
    storageState: { cookies: [], origins: [] },
  })
  const newUser = await context.newPage()
  await signUp(newUser, randomEmail(), randomPassword())
  await context.close()
}

test.describe("Onboarding stats page", () => {
  test("Superuser opens the stats page from the sidebar", async ({ page }) => {
    await page.goto("/")
    await page.getByRole("link", { name: "Onboarding" }).click()

    await expect(page).toHaveURL(/\/onboarding$/)
    await expect(
      page.getByRole("heading", { name: "Onboarding" }),
    ).toBeVisible()
  })

  test("Defaults to the last 30 days and shows the three numbers", async ({
    page,
    browser,
  }) => {
    await signUpInFreshContext(browser)
    await page.goto("/onboarding")

    await expect(page.getByLabel("From", { exact: true })).toHaveValue(
      localDate(daysAgo(30)),
    )
    await expect(page.getByLabel("To", { exact: true })).toHaveValue(
      localDate(new Date()),
    )
    await expect(page.getByTestId("stat-registered")).toHaveText(/^[1-9]\d*$/)
    await expect(page.getByTestId("stat-completed")).toHaveText(/^\d+$/)
    await expect(page.getByTestId("stat-rate")).toHaveText(/^\d+(\.\d)?%$/)
  })

  test("Changing the date range updates the numbers", async ({
    page,
    browser,
  }) => {
    await signUpInFreshContext(browser)
    await page.goto("/onboarding")
    await expect(page.getByTestId("stat-registered")).toHaveText(/^[1-9]\d*$/)

    await page.getByLabel("From", { exact: true }).fill("2000-01-01")
    await page.getByLabel("To", { exact: true }).fill("2000-01-31")

    await expect(page.getByTestId("stat-registered")).toHaveText("0")
    await expect(page.getByTestId("stat-completed")).toHaveText("0")
    await expect(page.getByTestId("stat-rate")).toHaveText("0%")
  })

  test("Shows the understated note only for windows ending within 7 days", async ({
    page,
  }) => {
    await page.goto("/onboarding")
    await expect(page.getByText(understatedNote)).toBeVisible()

    await page.getByLabel("To", { exact: true }).fill(localDate(daysAgo(10)))
    await expect(page.getByText(understatedNote)).not.toBeVisible()

    await page.getByLabel("To", { exact: true }).fill(localDate(daysAgo(3)))
    await expect(page.getByText(understatedNote)).toBeVisible()
  })
})

test.describe("Onboarding stats access control", () => {
  test.use({ storageState: { cookies: [], origins: [] } })

  test("Normal user sees no link and cannot open the page", async ({
    page,
  }) => {
    const email = randomEmail()
    const password = randomPassword()
    await createUser({ email, password })
    await logInUser(page, email, password)

    await expect(page.getByRole("link", { name: "Onboarding" })).toHaveCount(0)

    await page.goto("/onboarding")
    await expect(page).not.toHaveURL(/\/onboarding/)
    await expect(page.getByTestId("stat-registered")).not.toBeVisible()
  })
})
