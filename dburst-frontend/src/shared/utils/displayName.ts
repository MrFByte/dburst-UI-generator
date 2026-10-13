interface NamedUser {
  name?: string | null;
  email?: string | null;
}

/** The part of an email before "@" ("ada" for ada@example.com). */
export function emailLocalPart(email?: string | null): string {
  return (email ?? "").split("@")[0].trim();
}

/** What to call the user when they haven't set a name (e.g. email-OTP signups). */
export function displayName(user?: NamedUser | null): string {
  return user?.name?.trim() || emailLocalPart(user?.email) || "Account";
}
