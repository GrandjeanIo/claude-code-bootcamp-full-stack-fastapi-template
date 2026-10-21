import { Text } from "@react-email/components"
import { LinkButton } from "../ui/Button"
import { Heading } from "../ui/Heading"
import { Layout } from "../ui/Layout"
import { Link } from "../ui/Link"

type InviteProps = {
  project_name: string
  link: string
}

export default function Invite({
  project_name = "{{ project_name }}",
  link = "{{ link }}",
}: InviteProps) {
  return (
    <Layout
      title={`${project_name} - Invitation`}
      preview={`You have been invited to ${project_name}`}
      project_name={project_name}
    >
      <Heading>You're invited to {project_name}</Heading>
      <Text style={bodyTextStyle}>Hi,</Text>
      <Text style={bodyTextStyle}>
        Someone using {project_name} has invited you to join. Create your
        account to get started:
      </Text>
      <LinkButton href={link}>Sign Up</LinkButton>
      <Text style={supportingTextStyle}>
        Or copy and paste this link into your browser:
        <br />
        <Link href={link}>{link}</Link>
      </Text>
      <Text style={supportingTextStyle}>
        If you weren't expecting this invitation, you can ignore this email.
      </Text>
    </Layout>
  )
}

const bodyTextStyle = {
  color: "#334155",
  fontSize: "15px",
  lineHeight: "26px",
  margin: "0 0 18px",
}

const supportingTextStyle = {
  color: "#64748b",
  fontSize: "14px",
  lineHeight: "23px",
  margin: "0 0 16px",
}
