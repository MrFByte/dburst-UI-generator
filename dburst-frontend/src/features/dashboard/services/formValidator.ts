export const validate = () => {
    let valid = true;
    const newErrors = { title: "" };

    if (!title.trim()) {
      newErrors.title = "Project name is required.";
      valid = false;
    } else if (title.length > MAX_TITLE_LENGTH) {
      newErrors.title = "Project name must be under 200 characters.";
      valid = false;
    }

    setErrors(newErrors);
    return valid;
  };