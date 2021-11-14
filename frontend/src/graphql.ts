export class Server {
    request(query: string, variables?: object) {
        return fetch(
            "/graphql/",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ query, variables })
            }
        )
            .then((res) => res.json())
            .then((res) => {
                console.log(res);
                if (res.errors) {
                    throw res.errors;
                }
                return res.data;
            });
    }
}
