import { useEffect, useId, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import type { FormEvent, KeyboardEvent } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { X, Loader2 } from 'lucide-react';
import type { RootState } from '@/core/redux/store';
import type { User } from '@/core/redux/authSlice';
import { setUser } from '@/core/redux/authSlice';
import type { ApiError } from '@/core/api/apiHandler';
import { updateProfile } from '@/features/index/api/indexApi';
import type { ProfileUpdatePayload } from '@/features/index/api/indexApi';
import Avatar from '@/shared/components/Avatar';
import { toast } from '@/shared/hooks/useToast';
import { displayName, emailLocalPart } from '@/shared/utils/displayName';
import {
  AVATAR_URL_MAX_LENGTH,
  NAME_MAX_LENGTH,
  cleanName,
  validateAvatarUrl,
  validateName,
} from '../lib/profileValidation';

interface ProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
}

type FieldErrors = { name?: string; avatar_url?: string };

const FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]), textarea:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';

const ProfileModal = ({ isOpen, onClose }: ProfileModalProps) => {
  const user = useSelector((state: RootState) => state.auth.user);
  if (!isOpen || !user) return null;
  // Mounted fresh on every open, so the form always starts from the current
  // user. Portaled to <body>: it's opened from inside the header, whose
  // backdrop-filter makes it the containing block for `position: fixed`
  // descendants, which squeezed the overlay into the 64px header bar.
  return createPortal(<ProfileDialog user={user} onClose={onClose} />, document.body);
};

function firstError(details: unknown, field: string): string | undefined {
  const value = (details as Record<string, unknown> | undefined)?.[field];
  if (Array.isArray(value) && typeof value[0] === 'string') return value[0];
  if (typeof value === 'string') return value;
  return undefined;
}

function ProfileDialog({ user, onClose }: { user: User; onClose: () => void }) {
  const dispatch = useDispatch();
  const titleId = useId();
  const nameId = useId();
  const urlId = useId();
  const dialogRef = useRef<HTMLDivElement>(null);
  const nameInputRef = useRef<HTMLInputElement>(null);

  // Accounts created via email OTP have no name yet: suggest the email's
  // local part. It differs from the stored (empty) name, so Save is enabled.
  const [name, setName] = useState(() => user.name?.trim() ? user.name : emailLocalPart(user.email));
  const [avatarUrl, setAvatarUrl] = useState(user.avatar_url ?? '');
  const [serverErrors, setServerErrors] = useState<FieldErrors>({});
  const [touched, setTouched] = useState<{ name?: boolean; avatar_url?: boolean }>({});
  const [submitAttempted, setSubmitAttempted] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const nameClientError = validateName(name) ?? undefined;
  const urlClientError = validateAvatarUrl(avatarUrl) ?? undefined;
  // Client-side errors only show once the field was touched (edited or
  // blurred) or a save was attempted; server errors always show.
  const nameError = serverErrors.name ?? (touched.name || submitAttempted ? nameClientError : undefined);
  const urlError = serverErrors.avatar_url ?? (touched.avatar_url || submitAttempted ? urlClientError : undefined);

  const cleanedName = cleanName(name);
  const trimmedUrl = avatarUrl.trim();
  const nameChanged = cleanedName !== (user.name ?? '');
  const urlChanged = trimmedUrl !== (user.avatar_url ?? '');
  const isValid = !nameClientError && !urlClientError && !serverErrors.name && !serverErrors.avatar_url;
  const canSave = (nameChanged || urlChanged) && isValid && !isSaving;

  // Focus the first field on open, give focus back to whatever opened the
  // modal on close, and stop the page behind from scrolling.
  useEffect(() => {
    const previouslyFocused = document.activeElement as HTMLElement | null;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    nameInputRef.current?.focus();
    return () => {
      document.body.style.overflow = previousOverflow;
      if (previouslyFocused?.isConnected) previouslyFocused.focus();
    };
  }, []);

  const handleKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
    if (e.key === 'Escape') {
      e.stopPropagation();
      onClose();
      return;
    }
    if (e.key !== 'Tab' || !dialogRef.current) return;

    // Keep Tab / Shift+Tab inside the dialog.
    const focusables = Array.from(dialogRef.current.querySelectorAll<HTMLElement>(FOCUSABLE));
    if (focusables.length === 0) return;
    const first = focusables[0];
    const last = focusables[focusables.length - 1];
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitAttempted(true);
    if (!canSave) return;

    const payload: ProfileUpdatePayload = {};
    if (nameChanged) payload.name = cleanedName;
    if (urlChanged) payload.avatar_url = trimmedUrl || null;

    setIsSaving(true);
    try {
      const data = await updateProfile(payload);
      dispatch(setUser(data.user));
      toast.success('Profile updated');
      onClose();
    } catch (err) {
      const error = err as ApiError;
      const fieldErrors: FieldErrors = {
        name: firstError(error.details, 'name'),
        avatar_url: firstError(error.details, 'avatar_url'),
      };
      if (error.status === 400 && (fieldErrors.name || fieldErrors.avatar_url)) {
        setServerErrors(fieldErrors);
      } else {
        toast.error(error.status === 429 ? 'Too many updates. Please wait a minute.' : error.message || 'Failed to update profile');
      }
    } finally {
      setIsSaving(false);
    }
  };

  const inputClass = (hasError: boolean) =>
    `w-full min-h-11 rounded-xl px-4 py-2.5 text-base sm:text-[14px] outline-none transition-colors bg-[#1c1c1c] text-[#e8e8e8] placeholder:text-[#555] border ${
      hasError ? 'border-red-500/70 focus:border-red-400' : 'border-[#272727] focus:border-[#3a5cf5]'
    }`;

  return (
    <div
      className="fixed inset-0 z-[90] h-dvh flex items-end sm:items-center justify-center sm:p-4 bg-black/85 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onKeyDown={handleKeyDown}
        onClick={(e) => e.stopPropagation()}
        className="w-full sm:max-w-md max-h-[100dvh] sm:max-h-[calc(100dvh-2rem)] overflow-y-auto overscroll-contain rounded-t-2xl sm:rounded-2xl bg-[#171717] border border-[#2a2a2a] pb-[env(safe-area-inset-bottom)]"
      >
        {/* Header */}
        <div className="relative px-4 sm:px-6 pt-5 sm:pt-6 pb-4 pr-16 border-b border-[#222]">
          <p className="mb-1 text-[11px] font-medium uppercase tracking-widest text-[#666]">Account</p>
          <h2 id={titleId} className="text-[20px] font-semibold text-[#f5f5f5]">Your profile</h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close profile"
            className="absolute top-3 right-3 sm:top-5 sm:right-5 flex items-center justify-center w-11 h-11 sm:w-9 sm:h-9 rounded-lg bg-[#252525] border border-[#2e2e2e] text-[#999] hover:bg-[#2e2e2e] hover:text-[#f5f5f5] transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} noValidate className="px-4 sm:px-6 pt-5 pb-5 sm:pb-6 flex flex-col gap-5">
          {/* Preview */}
          <div className="flex items-center gap-4 min-w-0">
            <Avatar
              src={!validateAvatarUrl(avatarUrl) ? trimmedUrl : null}
              name={cleanedName || displayName(user)}
              alt="Avatar preview"
              className="w-16 h-16 text-2xl"
            />
            <div className="min-w-0">
              <p className="text-[15px] font-medium text-[#f5f5f5] truncate">{cleanedName || displayName(user)}</p>
              <p className="text-[13px] text-[#888] truncate">{user.email}</p>
            </div>
          </div>

          {/* Email (read-only) */}
          <div>
            <label htmlFor={`${nameId}-email`} className="block mb-2 text-[11px] font-medium uppercase tracking-wider text-[#666]">
              Email
            </label>
            <input
              id={`${nameId}-email`}
              type="email"
              value={user.email}
              readOnly
              aria-readonly="true"
              className="w-full min-h-11 rounded-xl px-4 py-2.5 text-base sm:text-[14px] bg-[#141414] text-[#888] border border-[#222] cursor-not-allowed outline-none"
            />
          </div>

          {/* Name */}
          <div>
            <div className="flex justify-between items-end mb-2">
              <label htmlFor={nameId} className="text-[11px] font-medium uppercase tracking-wider text-[#666]">
                Name
              </label>
              <span className={`text-[10px] ${cleanedName.length > NAME_MAX_LENGTH ? 'text-red-400' : 'text-[#444]'}`}>
                {cleanedName.length}/{NAME_MAX_LENGTH}
              </span>
            </div>
            <input
              ref={nameInputRef}
              id={nameId}
              type="text"
              autoComplete="name"
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                setTouched((prev) => ({ ...prev, name: true }));
                setServerErrors((prev) => ({ ...prev, name: undefined }));
              }}
              onBlur={() => setTouched((prev) => ({ ...prev, name: true }))}
              aria-invalid={!!nameError}
              aria-describedby={nameError ? `${nameId}-error` : undefined}
              className={inputClass(!!nameError)}
            />
            {nameError && (
              <p id={`${nameId}-error`} className="mt-1.5 text-[12px] text-red-400">{nameError}</p>
            )}
          </div>

          {/* Avatar URL */}
          <div>
            <label htmlFor={urlId} className="block mb-2 text-[11px] font-medium uppercase tracking-wider text-[#666]">
              Avatar image URL
            </label>
            <input
              id={urlId}
              type="url"
              inputMode="url"
              autoComplete="photo"
              placeholder="https://example.com/me.png"
              maxLength={AVATAR_URL_MAX_LENGTH}
              value={avatarUrl}
              onChange={(e) => {
                setAvatarUrl(e.target.value);
                setTouched((prev) => ({ ...prev, avatar_url: true }));
                setServerErrors((prev) => ({ ...prev, avatar_url: undefined }));
              }}
              onBlur={() => setTouched((prev) => ({ ...prev, avatar_url: true }))}
              aria-invalid={!!urlError}
              aria-describedby={`${urlId}-help${urlError ? ` ${urlId}-error` : ''}`}
              className={inputClass(!!urlError)}
            />
            <p id={`${urlId}-help`} className="mt-1.5 text-[12px] text-[#777]">
              Link to a public http(s) image. Leave empty to use your initial.
            </p>
            {urlError && (
              <p id={`${urlId}-error`} className="mt-1 text-[12px] text-red-400">{urlError}</p>
            )}
          </div>

          {/* Actions */}
          <div className="flex gap-2.5 pt-1">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 min-h-11 cursor-pointer rounded-xl text-[14px] font-medium transition-colors bg-transparent border border-[#2a2a2a] text-[#888] hover:bg-[#1e1e1e] hover:text-[#ccc] hover:border-[#333]"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!canSave}
              className="flex-[2] min-h-11 cursor-pointer rounded-xl text-[14px] font-semibold transition-colors flex items-center justify-center gap-2 bg-[#3a5cf5] text-white hover:bg-[#4f6ef7] disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-[#3a5cf5]"
            >
              {isSaving ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Saving...
                </>
              ) : (
                'Save'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default ProfileModal;
