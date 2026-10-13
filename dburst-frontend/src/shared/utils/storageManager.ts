/**
 * localStorage helpers for non-sensitive UI data only (e.g. the
 * "lastGeneratedProject" cache). Auth state never lives here: sessions are
 * httpOnly cookies the frontend cannot read. Keys that look auth-related are
 * refused outright so nobody reintroduces token storage through this module.
 */
export type JsonValue = string | number | boolean | object | null;

const FORBIDDEN_KEY = /token|auth|session|jwt|refresh|access|csrf|persist:root/i;

const isAllowedKey = (key: string): boolean => {
  if (FORBIDDEN_KEY.test(key)) {
    console.error(`storageManager: refusing auth-like key "${key}"`);
    return false;
  }
  return true;
};


export const setItem = <T extends JsonValue>(key: string, value: T): void => {
  if (!isAllowedKey(key)) return;
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (err) {
    console.error(`LocalStorage setItem error for key "${key}"`, err);
  }
};


export const getItem = <T = any>(key: string): T | null => {
  if (!isAllowedKey(key)) return null;
  try {
    const value = localStorage.getItem(key);
    if (!value) return null;
    return JSON.parse(value) as T;
  } catch (err) {
    console.error(`LocalStorage getItem error for key "${key}"`, err);
    return null;
  }
};


export const updateItem = <T extends Record<string, any>>(
  key: string,
  updatedValues: Partial<T>
): void => {
  try {
    const existing = getItem<T>(key);
    if (existing && typeof existing === "object") {
      const merged = { ...existing, ...updatedValues };
      setItem(key, merged);
    } else {
      console.warn(`LocalStorage updateItem: key "${key}" has no object value.`);
      setItem(key, updatedValues as T);
    }
  } catch (err) {
    console.error(`LocalStorage updateItem error for key "${key}"`, err);
  }
};


export const removeItem = (key: string): void => {
  try {
    localStorage.removeItem(key);
  } catch (err) {
    console.error(`LocalStorage removeItem error for key "${key}"`, err);
  }
};
