FROM node:22-alpine AS deps

WORKDIR /app

# Install all dependencies for deterministic builds. The final image uses the
# Next.js standalone output, not this full node_modules tree.
COPY package.json package-lock.json ./
RUN npm ci

FROM node:22-alpine AS builder

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Keep the existing security patch before build, then produce standalone output.
RUN node scripts/security/patch-next-picomatch.js \
    && npm run build

FROM node:22-alpine AS runner

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

WORKDIR /app

# Copy only the standalone server and static assets required at runtime.
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

# npm is not needed to run the standalone Next.js server.
RUN rm -rf /usr/local/lib/node_modules/npm /usr/local/bin/npm /usr/local/bin/npx

EXPOSE 3000

CMD ["node", "server.js"]
