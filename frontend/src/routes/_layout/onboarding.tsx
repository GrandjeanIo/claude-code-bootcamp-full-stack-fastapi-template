import { useQuery } from "@tanstack/react-query"
import { createFileRoute, redirect } from "@tanstack/react-router"
import { useState } from "react"

import { OnboardingService, UsersService } from "@/client"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

const DEFAULT_WINDOW_DAYS = 30
const COMPLETION_DAYS = 7
const DAY_MS = 24 * 60 * 60 * 1000

export const Route = createFileRoute("/_layout/onboarding")({
  component: OnboardingStatsPage,
  beforeLoad: async () => {
    const { data: user } = await UsersService.readUserMe()
    if (!user.is_superuser) {
      throw redirect({
        to: "/",
      })
    }
  },
  head: () => ({
    meta: [
      {
        title: "Onboarding - FastAPI Template",
      },
    ],
  }),
})

// "YYYY-MM-DD" in local time, the format of <input type="date">.
function toDateInput(date: Date) {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, "0")
  const d = String(date.getDate()).padStart(2, "0")
  return `${y}-${m}-${d}`
}

// Local midnight at the start of the given "YYYY-MM-DD" day.
function startOfDay(value: string) {
  const [y, m, d] = value.split("-").map(Number)
  return new Date(y, m - 1, d)
}

function Stat({
  label,
  value,
  testId,
}: {
  label: string
  value: string
  testId: string
}) {
  return (
    <div className="rounded-lg border p-4">
      <dt className="text-sm text-muted-foreground">{label}</dt>
      <dd className="text-2xl font-semibold" data-testid={testId}>
        {value}
      </dd>
    </div>
  )
}

function OnboardingStatsPage() {
  const [from, setFrom] = useState(() => {
    const d = new Date()
    d.setDate(d.getDate() - DEFAULT_WINDOW_DAYS)
    return toDateInput(d)
  })
  const [to, setTo] = useState(() => toDateInput(new Date()))

  // The "To" day is inclusive: the window ends at the start of the next day.
  const valid = Boolean(from && to)
  const start = valid ? startOfDay(from) : null
  const end = valid ? startOfDay(to) : null
  end?.setDate(end.getDate() + 1)

  const { data: stats } = useQuery({
    queryKey: ["onboarding-stats", from, to],
    queryFn: async () =>
      (
        await OnboardingService.readOnboardingStats({
          query: { start: start?.toISOString(), end: end?.toISOString() },
        })
      ).data,
    enabled: valid,
  })

  const understated =
    end !== null && end.getTime() > Date.now() - COMPLETION_DAYS * DAY_MS

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Onboarding</h1>
        <p className="text-muted-foreground">
          New users who completed onboarding within {COMPLETION_DAYS} days of
          registering
        </p>
      </div>
      <div className="flex flex-wrap gap-4">
        <div className="flex flex-col gap-2">
          <Label htmlFor="onboarding-from">From</Label>
          <Input
            id="onboarding-from"
            type="date"
            value={from}
            onChange={(e) => setFrom(e.target.value)}
          />
        </div>
        <div className="flex flex-col gap-2">
          <Label htmlFor="onboarding-to">To</Label>
          <Input
            id="onboarding-to"
            type="date"
            value={to}
            onChange={(e) => setTo(e.target.value)}
          />
        </div>
      </div>
      {stats && (
        <dl className="grid gap-4 sm:grid-cols-3">
          <Stat
            label="Registered"
            value={String(stats.registered)}
            testId="stat-registered"
          />
          <Stat
            label={`Completed within ${COMPLETION_DAYS} days`}
            value={String(stats.completed_within_7d)}
            testId="stat-completed"
          />
          <Stat
            label="Completion rate"
            value={`${Math.round(stats.completion_rate * 100) / 10}%`}
            testId="stat-rate"
          />
        </dl>
      )}
      {understated && (
        <p className="text-sm text-muted-foreground">
          The completion rate may be understated: this window ends within{" "}
          {COMPLETION_DAYS} days of now, so recent users are still inside their{" "}
          {COMPLETION_DAYS} days.
        </p>
      )}
    </div>
  )
}
