# Local fake of the shared helper library; only used by offline tests.
SA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SA_STATE="${SA_STATE:?test must provide temporary SA_STATE}"
sa_alias() {
  case "$1" in
    deepseek|eco-deepseek) printf '%s\n' eco-deepseek;;
    muse|eco-muse) printf '%s\n' eco-muse;;
    gemini|eco-gemini) printf '%s\n' eco-gemini;;
    gemini-eleve|eco-gemini-eleve) printf '%s\n' eco-gemini-eleve;;
    *) return 1;;
  esac
}
