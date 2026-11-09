export function getErrorMessage(error, fallback = 'Something went wrong. Please try again.') {
  const detail = error?.response?.data?.detail
  if (typeof detail === 'string' && detail.trim()) return detail
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => (typeof item === 'string' ? item : item?.msg))
      .filter(Boolean)
    if (messages.length) return messages.join(', ')
  }
  if (error?.code === 'ECONNABORTED') {
    return 'The request took too long. Try a smaller document or check the API connection.'
  }
  if (error?.request && !error?.response) {
    return 'Could not reach the Roleprint API. Check that the server is running, then try again.'
  }
  return fallback
}
