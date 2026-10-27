FROM node:22-alpine
WORKDIR /app
RUN npm install --global pnpm@9.15.9
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml /app/
COPY apps/web/package.json /app/apps/web/package.json
COPY packages/api-client/package.json /app/packages/api-client/package.json
RUN pnpm install --frozen-lockfile
COPY apps/web /app/apps/web
COPY packages/api-client /app/packages/api-client
WORKDIR /app/apps/web
CMD ["pnpm", "dev"]
