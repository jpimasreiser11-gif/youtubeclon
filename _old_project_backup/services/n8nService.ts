export const callN8nWebhook = async (message: string, webhookUrl: string, history: any[] = []): Promise<string> => {
    try {
        const response = await fetch(webhookUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message,
                history,
                timestamp: new Date().toISOString()
            }),
        });

        if (!response.ok) {
            throw new Error(`n8n webhook failed: ${response.statusText}`);
        }

        const data = await response.json();

        // Expecting data to have an 'output' or 'text' field, or just return the text.
        // Adjust based on your specific n8n workflow response structure.
        return data.output || data.text || data.message || JSON.stringify(data);
    } catch (error) {
        console.error("Error calling n8n:", error);
        return "Sorry, I couldn't connect to your n8n workflow. Please check your settings.";
    }
};
