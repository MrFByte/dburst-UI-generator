export type JsonValue = string | number | boolean | object | null;


export const setItem = <T extends JsonValue>(key: string, value: T): void => {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (err) {
    console.error(`LocalStorage setItem error for key "${key}"`, err);
  }
};


export const getItem = <T = any>(key: string): T | null => {
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
