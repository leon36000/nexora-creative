/** A director summary is only relevant while its original user prompt is still active. */
export function resumeCorrespondAIntention(intentionDuResume: string, intentionActuelle: string): boolean {
  const source = intentionDuResume.trim();
  return source.length > 0 && source === intentionActuelle.trim();
}
