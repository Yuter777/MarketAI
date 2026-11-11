module.exports = {
  apps: [
    {
      name: 'humo-forwarder',
      script: 'src/index.js',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '200M',
      restart_delay: 5000,
      max_restarts: 10,
      env: {
        NODE_ENV: 'production',
      },
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      error_file: 'logs/error.log',
      out_file: 'logs/out.log',
      merge_logs: true,
    },
  ],
};
