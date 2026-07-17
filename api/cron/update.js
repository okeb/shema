/**
 * Vercel Cron — mise à jour Bible BJC
 * Déclenche le workflow GitHub Actions qui clone GitLab et met à jour les JSON.
 *
 * Cron schedule : 0 6 * * 0 (dimanche 6h UTC)
 * Env vars requises :
 *   - CRON_SECRET  : généré automatiquement par Vercel (disponible en production)
 *   - GH_PAT       : GitHub Personal Access Token (scope : workflow)
 */
module.exports = async function handler(req, res) {
  // Vercel envoie automatiquement Authorization: Bearer <CRON_SECRET>
  const authHeader = req.headers["authorization"];
  if (authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
    return res.status(401).json({ error: "Non autorisé" });
  }

  const owner = process.env.VERCEL_GIT_REPO_OWNER;
  const repo  = process.env.VERCEL_GIT_REPO_SLUG;

  if (!owner || !repo) {
    return res.status(500).json({ error: "VERCEL_GIT_REPO_OWNER / SLUG non définis" });
  }
  if (!process.env.GH_PAT) {
    return res.status(500).json({ error: "GH_PAT non défini" });
  }

  const response = await fetch(
    `https://api.github.com/repos/${owner}/${repo}/actions/workflows/update-bible.yml/dispatches`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${process.env.GH_PAT}`,
        Accept: "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ ref: "master" }),
    }
  );

  if (!response.ok) {
    const details = await response.text();
    console.error("GitHub dispatch échoué :", details);
    return res.status(500).json({ error: "Déclenchement GitHub échoué", details });
  }

  console.log(`[cron] workflow update-bible.yml déclenché sur ${owner}/${repo}`);
  return res.status(200).json({ ok: true, message: "Workflow GitHub déclenché" });
};
