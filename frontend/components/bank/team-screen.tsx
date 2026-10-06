"use client"

import { useState, type FormEvent } from "react"
import { HugeiconsIcon } from "@hugeicons/react"
import { UserAdd01Icon, UserMultiple02Icon } from "@hugeicons/core-free-icons"
import {
  createBankStaff,
  listBankStaff,
  resetBankStaffPassword,
  setBankStaffPermissions,
  updateBankStaff,
} from "@/actions/bank"
import { bankPermissions, rolePermissions, staffRoles } from "@/config/bank"
import { useBankAccess } from "@/hooks/use-bank-access"
import { useMutation } from "@/hooks/use-mutation"
import { useQuery } from "@/hooks/use-query"
import { ActionError, ConfirmButton } from "@/components/bank/action-kit"
import { TableSkeleton } from "@/components/bank/data-table"
import { SelectFilter } from "@/components/bank/filters"
import { PageHeader, Section } from "@/components/bank/page-header"
import { QueryState } from "@/components/bank/query-state"
import { StatusBadge } from "@/components/bank/status-badge"
import { EmptyState } from "@/components/shared/empty-state"
import { Alert } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Dialog } from "@/components/ui/dialog"
import { Field } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import type { BankStaff, BankStaffRole } from "@/types"
import { formatDateTime } from "@/utils/format"

const noArgs: [] = []
const PASSWORD_MIN = 12
const PASSWORD_MAX = 72

const roleLabel = (role: BankStaffRole) => staffRoles.find((option) => option.value === role)?.label ?? role

function passwordError(password: string) {
  if (password.length < PASSWORD_MIN) return `Use at least ${PASSWORD_MIN} characters`
  if (password.length > PASSWORD_MAX) return `Use at most ${PASSWORD_MAX} characters`
  return undefined
}

// B12. bank administrators provision colleagues and decide what each can do.
// the api enforces every permission; this screen only edits them
export function TeamScreen() {
  const team = useQuery(listBankStaff, noArgs)
  const { session } = useBankAccess()
  const [adding, setAdding] = useState(false)
  const [created, setCreated] = useState<BankStaff | null>(null)

  return (
    <>
      <PageHeader
        title="Team"
        description="Who at your bank can use this console, and what each of them can do."
        actions={
          <Button
            type="button"
            title="Give a colleague access to this console"
            onClick={() => {
              setCreated(null)
              setAdding(true)
            }}
          >
            <HugeiconsIcon icon={UserAdd01Icon} size={18} strokeWidth={2.2} />
            Add colleague
          </Button>
        }
      />

      <div className="flex flex-col gap-10">
        {created && (
          <Alert variant="info" title={`${created.name ?? created.email} can now sign in`}>
            Share the temporary password with them directly. It isn&apos;t shown again.
          </Alert>
        )}

        <Section title="Staff">
          <QueryState
            query={team}
            noun="your team"
            skeleton={<TableSkeleton rows={3} />}
            isEmpty={(rows) => rows.length === 0}
            empty={<EmptyState icon={UserMultiple02Icon} title="No staff yet" />}
          >
            {(rows) => (
              <ul className="flex flex-col gap-3">
                {rows.map((staff) => (
                  <li key={staff.staff_id}>
                    <StaffCard
                      staff={staff}
                      isSelf={staff.user_id === session?.userId}
                      onChanged={(updated) => team.setData(rows.map((row) => (row.staff_id === updated.staff_id ? updated : row)))}
                    />
                  </li>
                ))}
              </ul>
            )}
          </QueryState>
        </Section>
      </div>

      <Dialog
        open={adding}
        onOpenChange={setAdding}
        title="Add a colleague"
        description="They sign in with this temporary password and your MFA phone, then change it."
        className="max-w-xl"
      >
        <CreateStaffForm
          onCancel={() => setAdding(false)}
          onCreated={(staff) => {
            setCreated(staff)
            setAdding(false)
            team.retry()
          }}
        />
      </Dialog>
    </>
  )
}

const emptyStaff = { name: "", email: "", mfa_phone: "", temporary_password: "" }

type CreateStaffFormProps = {
  onCreated: (staff: BankStaff) => void
  onCancel: () => void
}

function CreateStaffForm({ onCreated, onCancel }: CreateStaffFormProps) {
  const [values, setValues] = useState(emptyStaff)
  const [role, setRole] = useState<BankStaffRole | "">("bank_risk_analyst")
  const [errors, setErrors] = useState<Partial<Record<keyof typeof emptyStaff | "role", string>>>({})
  const create = useMutation(createBankStaff)

  function set(key: keyof typeof emptyStaff, value: string) {
    setValues((current) => ({ ...current, [key]: value }))
    if (errors[key]) setErrors((current) => ({ ...current, [key]: undefined }))
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const nextErrors = {
      name: values.name.trim() ? undefined : "Enter their name",
      email: /^[^\s@]+@[^\s@]+$/.test(values.email.trim()) ? undefined : "Enter their work email",
      mfa_phone: values.mfa_phone.trim().length >= 4 ? undefined : "Enter the phone that receives their sign-in codes",
      temporary_password: passwordError(values.temporary_password),
      role: role ? undefined : "Choose a role",
    }
    setErrors(nextErrors)
    if (Object.values(nextErrors).some(Boolean) || !role) return

    const result = await create.mutate({
      name: values.name.trim(),
      email: values.email.trim(),
      mfa_phone: values.mfa_phone.trim(),
      temporary_password: values.temporary_password,
      role,
    })
    if (result.ok) onCreated(result.data)
  }

  const fields: { key: keyof typeof emptyStaff; label: string; type?: string; placeholder: string }[] = [
    { key: "name", label: "Name", placeholder: "Their full name" },
    { key: "email", label: "Work email", type: "email", placeholder: "name@yourbank.com" },
    { key: "mfa_phone", label: "MFA phone", type: "tel", placeholder: "2348012345678" },
    { key: "temporary_password", label: "Temporary password", type: "password", placeholder: "At least 12 characters" },
  ]

  return (
    <form noValidate onSubmit={handleSubmit} className="flex flex-col gap-5">
      <div className="grid gap-4 sm:grid-cols-2">
        {fields.map((field) => {
          const id = `staff-${field.key}`
          return (
            <Field key={field.key} id={id} label={field.label} error={errors[field.key]}>
              <Input
                id={id}
                type={field.type ?? "text"}
                value={values[field.key]}
                onChange={(event) => set(field.key, event.target.value)}
                invalid={Boolean(errors[field.key])}
                aria-describedby={errors[field.key] ? `${id}-error` : undefined}
                autoComplete={field.type === "password" ? "new-password" : "off"}
                placeholder={field.placeholder}
                className="h-12 text-sm"
              />
            </Field>
          )
        })}
      </div>

      <SelectFilter
        id="staff-role"
        label="Role"
        value={role}
        onChange={setRole}
        options={staffRoles}
        allLabel="Choose a role"
        className="sm:w-full"
      />
      {role && (
        <p className="-mt-3 text-xs font-semibold text-muted-foreground">
          {staffRoles.find((option) => option.value === role)?.description}
        </p>
      )}

      <ActionError error={create.error} />

      <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
        <Button type="button" variant="ghost" onClick={onCancel} disabled={create.isPending}>
          Cancel
        </Button>
        <Button type="submit" loading={create.isPending}>
          Add colleague
        </Button>
      </div>
    </form>
  )
}

type StaffCardProps = {
  staff: BankStaff
  isSelf: boolean
  onChanged: (staff: BankStaff) => void
}

function StaffCard({ staff, isSelf, onChanged }: StaffCardProps) {
  const [open, setOpen] = useState(false)
  const update = useMutation(updateBankStaff)
  const active = staff.status === "active"

  async function setStatus(status: BankStaff["status"]) {
    const result = await update.mutate(staff.staff_id, { status })
    if (result.ok) onChanged(result.data)
  }

  return (
    <div className="card-raised flex flex-col gap-4 rounded-2xl p-4 sm:p-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <p className="text-base font-black">
            {staff.name ?? staff.email}
            {isSelf && <span className="ml-2 text-xs font-bold text-muted-foreground">(you)</span>}
          </p>
          <p className="font-mono text-xs font-semibold break-all text-muted-foreground">{staff.email}</p>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <StatusBadge status={staff.role} label={roleLabel(staff.role)} tone="indigo" />
            <StatusBadge status={staff.status} tone={active ? "gold" : "neutral"} />
            <span className="text-xs font-bold text-muted-foreground">
              Last sign in {formatDateTime(staff.last_login_at)}
            </span>
          </div>
        </div>
        {!isSelf && (
          <div className="flex shrink-0 flex-wrap gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              aria-expanded={open}
              title={open ? "close" : `manage ${staff.name ?? staff.email}'s role, permissions and password`}
              onClick={() => setOpen((value) => !value)}
            >
              {open ? "Close" : "Manage"}
            </Button>
            {active ? (
              <ConfirmButton
                confirmLabel="Yes, revoke access"
                variant="ghost"
                loading={update.isPending}
                onConfirm={() => setStatus("revoked")}
              >
                Revoke access
              </ConfirmButton>
            ) : (
              <Button type="button" variant="ghost" size="sm" loading={update.isPending} onClick={() => setStatus("active")}>
                Restore access
              </Button>
            )}
          </div>
        )}
      </div>

      <ActionError error={update.error} />

      {open && !isSelf && (
        <div className="flex flex-col gap-5 border-t-2 border-hairline pt-4">
          {/* keyed so a saved change resets each editor to what the api now holds */}
          <RoleEditor key={staff.role} staff={staff} onChanged={onChanged} />
          <PermissionsEditor key={`${staff.role}:${staff.permissions.join(",")}`} staff={staff} onChanged={onChanged} />
          <PasswordReset staff={staff} />
        </div>
      )}
    </div>
  )
}

function RoleEditor({ staff, onChanged }: { staff: BankStaff; onChanged: (staff: BankStaff) => void }) {
  const [role, setRole] = useState<BankStaffRole | "">(staff.role)
  const update = useMutation(updateBankStaff)

  async function handleSave() {
    if (!role || role === staff.role) return
    // a role change resets permissions to that role's defaults
    const result = await update.mutate(staff.staff_id, { role })
    if (result.ok) onChanged(result.data)
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
        <SelectFilter
          id={`role-${staff.staff_id}`}
          label="Role"
          value={role}
          onChange={setRole}
          options={staffRoles}
          allLabel="Choose a role"
          className="sm:w-72"
        />
        <Button
          type="button"
          size="sm"
          variant="outline"
          loading={update.isPending}
          disabled={!role || role === staff.role}
          onClick={handleSave}
        >
          Change role
        </Button>
      </div>
      <p className="text-xs font-semibold text-muted-foreground">Changing the role resets permissions to its defaults.</p>
      <ActionError error={update.error} />
    </div>
  )
}

function PermissionsEditor({ staff, onChanged }: { staff: BankStaff; onChanged: (staff: BankStaff) => void }) {
  const allowed = rolePermissions[staff.role] ?? []
  const [selected, setSelected] = useState<string[]>(staff.permissions)
  const save = useMutation(setBankStaffPermissions)
  const changed = selected.length !== staff.permissions.length || selected.some((value) => !staff.permissions.includes(value))

  async function handleSave() {
    const result = await save.mutate(staff.staff_id, selected)
    if (result.ok) onChanged({ ...staff, permissions: result.data.permissions })
  }

  return (
    <fieldset className="flex flex-col gap-3">
      <legend className="mb-2 text-sm font-extrabold">Permissions</legend>
      <p className="-mt-1 text-xs font-semibold text-muted-foreground">
        Narrow what this person can do within their role. Permissions outside the role can&apos;t be granted.
      </p>
      <div className="grid gap-3 sm:grid-cols-2">
        {bankPermissions
          .filter((permission) => allowed.includes(permission.value))
          .map((permission) => (
            <Checkbox
              key={permission.value}
              id={`perm-${staff.staff_id}-${permission.value}`}
              checked={selected.includes(permission.value)}
              onChange={(event) =>
                setSelected((current) =>
                  event.target.checked ? [...current, permission.value] : current.filter((value) => value !== permission.value)
                )
              }
              label={
                <>
                  <span className="font-extrabold text-foreground">{permission.label}</span>
                  <span className="block font-mono text-xs">{permission.value}</span>
                </>
              }
            />
          ))}
      </div>
      <ActionError error={save.error} />
      <Button
        type="button"
        size="sm"
        variant="outline"
        loading={save.isPending}
        disabled={!changed || selected.length === 0}
        onClick={handleSave}
        className="sm:self-start"
      >
        Save permissions
      </Button>
    </fieldset>
  )
}

function PasswordReset({ staff }: { staff: BankStaff }) {
  const [password, setPassword] = useState("")
  const [error, setError] = useState<string>()
  const [done, setDone] = useState(false)
  const reset = useMutation(resetBankStaffPassword)
  const id = `reset-${staff.staff_id}`

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const message = passwordError(password)
    setError(message)
    if (message) return
    const result = await reset.mutate(staff.staff_id, password)
    if (result.ok) {
      setPassword("")
      setDone(true)
    }
  }

  return (
    <form noValidate onSubmit={handleSubmit} className="flex flex-col gap-3">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
        <Field id={id} label="Reset password" error={error} className="sm:w-72">
          <Input
            id={id}
            type="password"
            autoComplete="new-password"
            value={password}
            onChange={(event) => {
              setPassword(event.target.value)
              setDone(false)
              if (error) setError(undefined)
            }}
            invalid={Boolean(error)}
            aria-describedby={error ? `${id}-error` : undefined}
            placeholder="A new temporary password"
            className="h-12 text-sm"
          />
        </Field>
        <Button type="submit" size="sm" variant="outline" loading={reset.isPending}>
          Reset password
        </Button>
      </div>
      <ActionError error={reset.error} />
      {done && (
        <Alert variant="info" title="Password reset">
          Every session they held has ended. Share the new password with them directly.
        </Alert>
      )}
    </form>
  )
}
