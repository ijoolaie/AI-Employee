FROM node:22-alpine AS deps
WORKDIR /app
COPY frontend/package.json ./package.json
COPY frontend/package-lock.json ./package-lock.json
RUN npm ci --no-audit --no-fund

FROM node:22-alpine AS builder
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
# Next.js rewrites are evaluated at build time, so provide the Docker-internal API target here.
ARG API_INTERNAL_URL=http://api:8000
ENV API_INTERNAL_URL=${API_INTERNAL_URL}
COPY --from=deps /app/node_modules ./node_modules
COPY frontend ./
RUN npm run test
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV HOSTNAME=0.0.0.0
RUN addgroup --system --gid 10001 nodejs && adduser --system --uid 10001 nextjs
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
USER nextjs
EXPOSE 3000
CMD ["node", "server.js"]
