FROM node:20-alpine

WORKDIR /app

COPY package.json .

# Installing dependencies
RUN npm install

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]
