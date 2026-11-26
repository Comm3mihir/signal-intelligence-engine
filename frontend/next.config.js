const backend = (process.env.SIGNAL_BACKEND_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

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
