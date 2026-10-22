const ACCESS_TOKEN_KEY = "access_token"

const getAccessToken = (): string | null =>
  localStorage.getItem(ACCESS_TOKEN_KEY) ??
  sessionStorage.getItem(ACCESS_TOKEN_KEY)

const setAccessToken = (token: string, remember: boolean) => {
  if (remember) {
    localStorage.setItem(ACCESS_TOKEN_KEY, token)
    sessionStorage.removeItem(ACCESS_TOKEN_KEY)
  } else {
    sessionStorage.setItem(ACCESS_TOKEN_KEY, token)
    localStorage.removeItem(ACCESS_TOKEN_KEY)
  }
}

const clearAccessToken = () => {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  sessionStorage.removeItem(ACCESS_TOKEN_KEY)
}

export { clearAccessToken, getAccessToken, setAccessToken }
