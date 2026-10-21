import { expect, type Page, test } from "@playwright/test"
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

async function invite(page: Page, email: string) {
  await page.getByLabel("Email to invite").fill(email)
  await page.getByRole("button", { name: "Send invite" }).click()
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
    await page.goto("/signup")
    await page.getByTestId("full-name-input").fill("Test User")
    await page.getByTestId("email-input").fill(email)
    await page.getByTestId("password-input").fill(password)
    await page.getByTestId("confirm-password-input").fill(password)
    await page.getByRole("button", { name: "Sign Up" }).click()
    await expect(page).toHaveURL(/\/login$/)
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
