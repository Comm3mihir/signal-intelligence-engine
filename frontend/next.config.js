const production = process.env.SIGNAL_ENV === "production" || Boolean(process.env.VERCEL);
const configured = process.env.SIGNAL_BACKEND_URL;
if (production) {
  const url = configured && new URL(configured);
  if (!url || url.protocol !== "https:" || url.username || url.password ||
      ["localhost", "127.0.0.1", "0.0.0.0", "[::1]"].includes(url.hostname)) {
    throw new Error("Use an HTTPS cloud API URL in SIGNAL_BACKEND_URL.");
  }
}
const backend = (configured || "http://127.0.0.1:8000").replace(/\/$/, "");

module.exports = {
  reactStrictMode: true,
  skipTrailingSlashRedirect: true,
  async rewrites() {
    return [
      { source: "/backend-health", destination: `${backend}/` },
      {
        source: "/api/:resource(intelligence|signals|risks|organisations|chat)/",
        destination: `${backend}/api/:resource/`,
      },
      { source: "/api/:path*", destination: `${backend}/api/:path*` },
    ];
  },
};
