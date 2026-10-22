import { expect, type Page, test } from "@playwright/test"
import { firstSuperuser, firstSuperuserPassword } from "./config.ts"
import { randomPassword } from "./utils/random.ts"

test.use({ storageState: { cookies: [], origins: [] } })

const fillForm = async (page: Page, email: string, password: string) => {
  await page.getByTestId("email-input").fill(email)
  await page.getByTestId("password-input").fill(password)
}

const readTokens = (page: Page) =>
  page.evaluate(() => ({
    local: localStorage.getItem("access_token"),
    session: sessionStorage.getItem("access_token"),
  }))

const tokenExpiryDays = (token: string) => {
  const payload = JSON.parse(
    Buffer.from(token.split(".")[1], "base64url").toString(),
  ) as { exp: number }
  return (payload.exp * 1000 - Date.now()) / (1000 * 60 * 60 * 24)
}

const nextLoginRequestBody = (page: Page) =>
  page
    .waitForRequest((request) =>
      request.url().endsWith("/api/v1/login/access-token"),
    )
    .then((request) => new URLSearchParams(request.postData() ?? ""))

const verifyInput = async (page: Page, testId: string) => {
  const input = page.getByTestId(testId)
  await expect(input).toBeVisible()
  await expect(input).toHaveText("")
  await expect(input).toBeEditable()
}

test("Inputs are visible, empty and editable", async ({ page }) => {
  await page.goto("/login")

  await verifyInput(page, "email-input")
  await verifyInput(page, "password-input")
})

test("Log In button is visible", async ({ page }) => {
  await page.goto("/login")

  await expect(page.getByRole("button", { name: "Log In" })).toBeVisible()
})

test("Forgot Password link is visible", async ({ page }) => {
  await page.goto("/login")

  await expect(
    page.getByRole("link", { name: "Forgot your password?" }),
  ).toBeVisible()
})

test("Remember me checkbox is visible and unchecked by default", async ({
  page,
}) => {
  await page.goto("/login")

  const checkbox = page.getByTestId("remember-me-checkbox")
  await expect(checkbox).toBeVisible()
  await expect(checkbox).not.toBeChecked()
  await expect(page.getByText("Remember me")).toBeVisible()
})

test("Log in with valid email and password ", async ({ page }) => {
  await page.goto("/login")

  await fillForm(page, firstSuperuser, firstSuperuserPassword)
  await page.getByRole("button", { name: "Log In" }).click()

  await page.waitForURL("/")

  await expect(
    page.getByText("Welcome back, nice to see you again!"),
  ).toBeVisible()
})

test("Log in with invalid email", async ({ page }) => {
  await page.goto("/login")

  await fillForm(page, "invalidemail", firstSuperuserPassword)
  await page.getByRole("button", { name: "Log In" }).click()

  await expect(page.getByText("Invalid email address")).toBeVisible()
})

test("Log in with invalid password", async ({ page }) => {
  const password = randomPassword()

  await page.goto("/login")
  await fillForm(page, firstSuperuser, password)
  await page.getByRole("button", { name: "Log In" }).click()

  await expect(page.getByText("Incorrect email or password")).toBeVisible()
})

test("Log in without remember me keeps an 8-day token in session storage", async ({
  page,
}) => {
  await page.goto("/login")

  await fillForm(page, firstSuperuser, firstSuperuserPassword)
  const loginRequest = nextLoginRequestBody(page)
  await page.getByRole("button", { name: "Log In" }).click()

  expect([null, "false"]).toContain((await loginRequest).get("remember_me"))

  await page.waitForURL("/")

  const tokens = await readTokens(page)
  expect(tokens.session).not.toBeNull()
  expect(tokens.local).toBeNull()
  expect(tokenExpiryDays(tokens.session ?? "")).toBeCloseTo(8, 0)
})

test("Log in with remember me keeps a 30-day token in local storage", async ({
  page,
}) => {
  await page.goto("/login")

  await fillForm(page, firstSuperuser, firstSuperuserPassword)
  await page.getByTestId("remember-me-checkbox").click()
  const loginRequest = nextLoginRequestBody(page)
  await page.getByRole("button", { name: "Log In" }).click()

  expect((await loginRequest).get("remember_me")).toBe("true")

  await page.waitForURL("/")

  const tokens = await readTokens(page)
  expect(tokens.local).not.toBeNull()
  expect(tokens.session).toBeNull()
  expect(tokenExpiryDays(tokens.local ?? "")).toBeCloseTo(30, 0)
})

test("Successful log out", async ({ page }) => {
  await page.goto("/login")

  await fillForm(page, firstSuperuser, firstSuperuserPassword)
  await page.getByTestId("remember-me-checkbox").click()
  await page.getByRole("button", { name: "Log In" }).click()

  await page.waitForURL("/")

  await expect(
    page.getByText("Welcome back, nice to see you again!"),
  ).toBeVisible()

  await page.getByTestId("user-menu").click()
  await page.getByRole("menuitem", { name: "Log out" }).click()
  await page.waitForURL("/login")

  const tokens = await readTokens(page)
  expect(tokens.local).toBeNull()
  expect(tokens.session).toBeNull()
})

test("Log out without remember me clears the session token", async ({
  page,
}) => {
  await page.goto("/login")

  await fillForm(page, firstSuperuser, firstSuperuserPassword)
  await page.getByRole("button", { name: "Log In" }).click()

  await page.waitForURL("/")

  await page.getByTestId("user-menu").click()
  await page.getByRole("menuitem", { name: "Log out" }).click()
  await page.waitForURL("/login")

  const tokens = await readTokens(page)
  expect(tokens.local).toBeNull()
  expect(tokens.session).toBeNull()
})

test("A token already in local storage counts as logged in", async ({
  page,
  request,
}) => {
  const response = await request.post(
    `${process.env.VITE_API_URL}/api/v1/login/access-token`,
    {
      form: { username: firstSuperuser, password: firstSuperuserPassword },
    },
  )
  const { access_token: token } = await response.json()

  await page.goto("/login")
  await page.evaluate((token) => {
    localStorage.setItem("access_token", token)
  }, token)

  await page.goto("/")
  await expect(
    page.getByText("Welcome back, nice to see you again!"),
  ).toBeVisible()
  await expect(page).toHaveURL("/")
})

test("Logged-out user cannot access protected routes", async ({ page }) => {
  await page.goto("/login")

  await fillForm(page, firstSuperuser, firstSuperuserPassword)
  await page.getByRole("button", { name: "Log In" }).click()

  await page.waitForURL("/")

  await expect(
    page.getByText("Welcome back, nice to see you again!"),
  ).toBeVisible()

  await page.getByTestId("user-menu").click()
  await page.getByRole("menuitem", { name: "Log out" }).click()
  await page.waitForURL("/login")

  await page.goto("/settings")
  await page.waitForURL("/login")
})

test("Redirects to /login when token is wrong", async ({ page }) => {
  await page.goto("/settings")
  await page.evaluate(() => {
    localStorage.setItem("access_token", "invalid_token")
  })
  await page.goto("/settings")
  await page.waitForURL("/login")
  await expect(page).toHaveURL("/login")
})
