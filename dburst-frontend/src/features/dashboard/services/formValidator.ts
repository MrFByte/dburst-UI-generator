const MAX_TITLE_LENGTH = 200;

export const validateProjectTitle = (title: string): string => {
  if (!title.trim()) {
    return "Project name is required.";
  }
  if (title.length > MAX_TITLE_LENGTH) {
    return "Project name must be under 200 characters.";
  }
  return "";
};
