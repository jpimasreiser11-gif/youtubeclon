// BYPASS AUTHENTICATION
// The user requested to remove login. We mock the auth() function to return a static admin user.
// This preserves the app logic (which needs a user ID for DB queries) without requiring Google Auth.

const MOCK_SESSION = {
    user: {
        id: "06038e52-625a-47cb-9158-4a5d405b2bd7",
        name: "J. Pima",
        email: "j.pima@example.com",
        image: null
    },
    expires: "9999-12-31T23:59:59.999Z"
};

export const auth = async () => {
    return MOCK_SESSION;
};

export const handlers = {
    GET: (req: Request) => new Response(JSON.stringify(MOCK_SESSION), {
        status: 200,
        headers: { "Content-Type": "application/json" }
    }),
    POST: (req: Request) => new Response(JSON.stringify(MOCK_SESSION), {
        status: 200,
        headers: { "Content-Type": "application/json" }
    })
};

export const signIn = async () => { };
export const signOut = async () => { };
