# BimaSarathi web — build the Vite SPA, serve it statically on $PORT.
# NOTE: Vite bakes VITE_* vars at BUILD time, so the backend URL must be known here.
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .

# Railway passes service variables as build args — declare and expose to the build.
ARG VITE_SUPABASE_URL
ARG VITE_SUPABASE_ANON_KEY
ARG VITE_ORCHESTRATOR_URL
ENV VITE_SUPABASE_URL=$VITE_SUPABASE_URL \
    VITE_SUPABASE_ANON_KEY=$VITE_SUPABASE_ANON_KEY \
    VITE_ORCHESTRATOR_URL=$VITE_ORCHESTRATOR_URL
RUN npm run build

FROM node:20-alpine
WORKDIR /app
RUN npm install -g serve
COPY --from=build /app/dist ./dist
# -s = SPA fallback to index.html; bind to Railway's $PORT
CMD ["sh", "-c", "serve -s dist -l ${PORT:-8080}"]
