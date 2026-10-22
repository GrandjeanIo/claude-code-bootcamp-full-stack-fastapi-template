import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useForm } from "react-hook-form"
import { z } from "zod"

import { OnboardingService } from "@/client"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { LoadingButton } from "@/components/ui/loading-button"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

const formSchema = z.object({
  email: z.email({ message: "Invalid email address" }),
})

type FormData = z.infer<typeof formSchema>

function Step({
  id,
  label,
  done,
}: {
  id: string
  label: string
  done: boolean
}) {
  return (
    <li className="flex items-center gap-2">
      <Checkbox id={id} checked={done} disabled />
      <Label htmlFor={id}>{label}</Label>
    </li>
  )
}

function InviteForm() {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: { email: "" },
  })

  const mutation = useMutation({
    mutationFn: (data: FormData) =>
      OnboardingService.sendInvite({ body: data }),
    onSuccess: () => {
      showSuccessToast("Invitation sent")
      form.reset()
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["onboarding"] })
    },
  })

  return (
    <Form {...form}>
      <form
        onSubmit={form.handleSubmit((data) => mutation.mutate(data))}
        className="flex items-end gap-2 pl-6"
      >
        <FormField
          control={form.control}
          name="email"
          render={({ field }) => (
            <FormItem className="flex-1 max-w-sm">
              <FormLabel>Email to invite</FormLabel>
              <FormControl>
                <Input
                  placeholder="friend@example.com"
                  type="email"
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <LoadingButton type="submit" loading={mutation.isPending}>
          Send invite
        </LoadingButton>
      </form>
    </Form>
  )
}

const OnboardingChecklist = () => {
  const { data: onboarding } = useQuery({
    queryKey: ["onboarding"],
    queryFn: async () => (await OnboardingService.readOnboardingMe()).data,
    retry: false,
  })

  if (!onboarding || onboarding.completed) {
    return null
  }

  return (
    <section
      aria-labelledby="onboarding-heading"
      className="mt-6 rounded-lg border p-4 space-y-4"
    >
      <h2 id="onboarding-heading" className="text-lg font-semibold">
        Get started
      </h2>
      <ul className="space-y-3">
        <Step
          id="onboarding-first-item"
          label="Create your first item"
          done={onboarding.first_item}
        />
        <Step
          id="onboarding-name-edited"
          label="Edit your profile name"
          done={onboarding.name_edited}
        />
        <Step
          id="onboarding-invite-sent"
          label="Invite someone by email"
          done={onboarding.invite_sent}
        />
      </ul>
      <InviteForm />
    </section>
  )
}

export default OnboardingChecklist
