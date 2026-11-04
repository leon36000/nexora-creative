/** Builds the supported Prolonger URL for a legacy /extend deep link. */
export function prolongerRedirect(params: URLSearchParams): string {
  const target = new URLSearchParams();
  if (params.get('mode') === 'transition') target.set('mode', 'raccord');
  const take = params.get('take');
  if (take !== null) target.set('take', take);
  const query = target.toString();
  return `/prolonger${query ? `?${query}` : ''}`;
}
