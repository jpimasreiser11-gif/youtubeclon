import NextAuth from "next-auth";
import PostgresAdapter from "@auth/pg-adapter";
import pool from "@/lib/db";
import authConfig from "./auth.config";

export const { handlers, auth, signIn, signOut } = NextAuth({
    adapter: PostgresAdapter(pool),
    session: { strategy: "jwt" },
    ...authConfig,
});
