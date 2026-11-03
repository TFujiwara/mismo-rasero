FROM node:20-alpine

WORKDIR /repo
RUN corepack enable

# NEXT_PUBLIC_* se inlinea en el bundle del navegador en BUILD TIME;
# la misma variable se aplica en runtime para los server components.
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

COPY pnpm-workspace.yaml package.json ./
COPY packages/web/package.json packages/web/package.json
RUN pnpm install --frozen-lockfile || pnpm install

COPY packages/web/ packages/web/
RUN pnpm --filter @blueprint/web build

EXPOSE 3000
CMD ["pnpm", "--filter", "@blueprint/web", "start"]
