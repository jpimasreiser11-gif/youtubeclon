import React, { useState, useEffect } from 'react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { useToast } from '../components/ToastProvider';

import { generateN8nWorkflow } from '../services/geminiService';

const SettingsScreen: React.FC = () => {
    const [webhookUrl, setWebhookUrl] = useState('');
    const [apiKey, setApiKey] = useState('');
    const [useN8n, setUseN8n] = useState(false);

    // Workflow Generator State
    const [workflowPrompt, setWorkflowPrompt] = useState('');
    const [generatedJson, setGeneratedJson] = useState<string | null>(null);
    const [isGenerating, setIsGenerating] = useState(false);

    const { showToast } = useToast();

    const handleGenerateWorkflow = async () => {
        setIsGenerating(true);
        setGeneratedJson(null);
        try {
            const json = await generateN8nWorkflow(workflowPrompt);
            setGeneratedJson(json);
            showToast('Workflow generated successfully!', 'success');
        } catch (e: any) {
            console.error(e);
            showToast(`Error: ${e.message || 'Failed to generate'}`, 'error');
        } finally {
            setIsGenerating(false);
        }
    };

    useEffect(() => {
        const savedWebhook = localStorage.getItem('n8n_webhook_url');
        const savedApiKey = localStorage.getItem('google_api_key');
        const savedUseN8n = localStorage.getItem('use_n8n') === 'true';

        if (savedWebhook) setWebhookUrl(savedWebhook);
        if (savedApiKey) setApiKey(savedApiKey);
        setUseN8n(savedUseN8n);
    }, []);

    const handleSave = () => {
        localStorage.setItem('n8n_webhook_url', webhookUrl);
        localStorage.setItem('google_api_key', apiKey); // Note: For demo purposes. In prod, use .env or secure storage.
        localStorage.setItem('use_n8n', useN8n.toString());

        // Optionally update env/service state here if needed
        // Assuming service reads from localStorage or we reload

        showToast('Settings saved successfully!', 'success');
    };

    return (
        <div className="flex-1 h-full overflow-y-auto bg-slate-50 dark:bg-slate-900/50 p-6 md:p-10">
            <div className="max-w-2xl mx-auto space-y-8">
                <header>
                    <h1 className="text-3xl font-black text-slate-900 dark:text-white mb-2">Settings</h1>
                    <p className="text-slate-500">Configure your AI integrations and preferences.</p>
                </header>

                <Card className="space-y-6">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="size-10 bg-orange-500/10 text-orange-600 rounded-lg flex items-center justify-center">
                                <span className="material-symbols-outlined">hub</span>
                            </div>
                            <div>
                                <h3 className="font-bold text-slate-900 dark:text-white">n8n Integration</h3>
                                <p className="text-xs text-slate-500">Connect to your workflow automation.</p>
                            </div>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                            <input type="checkbox" className="sr-only peer" checked={useN8n} onChange={(e) => setUseN8n(e.target.checked)} />
                            <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer dark:bg-slate-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                        </label>
                    </div>

                    {useN8n && (
                        <div className="space-y-4 pt-4 border-t border-slate-100 dark:border-slate-800 animate-in slide-in-from-top-2">
                            <Input
                                label="n8n Webhook URL (Chat)"
                                placeholder="https://your-n8n-instance.com/webhook/..."
                                value={webhookUrl}
                                onChange={(e) => setWebhookUrl(e.target.value)}
                                icon="link"
                            />
                            <div className="bg-blue-50 dark:bg-blue-500/10 p-4 rounded-lg flex gap-3 text-sm text-blue-700 dark:text-blue-300">
                                <span className="material-symbols-outlined text-blue-500">info</span>
                                <p>Ensure your n8n workflow accepts a JSON body with a <code className="bg-white/50 px-1 rounded font-mono font-bold">message</code> field and returns a JSON with <code className="bg-white/50 px-1 rounded font-mono font-bold">output</code> text.</p>
                            </div>
                        </div>
                    )}
                </Card>

                <Card className="space-y-6">
                    <div className="flex items-center gap-3 mb-4">
                        <div className="size-10 bg-blue-500/10 text-blue-600 rounded-lg flex items-center justify-center">
                            <span className="material-symbols-outlined">key</span>
                        </div>
                        <div>
                            <h3 className="font-bold text-slate-900 dark:text-white">API Configuration</h3>
                            <p className="text-xs text-slate-500">Manage your direct API keys.</p>
                        </div>
                    </div>
                    <Input
                        label="Google Gemini API Key"
                        type="password"
                        placeholder="AIzaSy..."
                        value={apiKey}
                        onChange={(e) => setApiKey(e.target.value)}
                        icon="vpn_key"
                    />
                </Card>



                {/* Workflow Generator Section */}
                <Card className="space-y-6 border-2 border-indigo-500/10 dark:border-indigo-500/20 bg-indigo-50/50 dark:bg-indigo-900/10">
                    <div className="flex items-center gap-3">
                        <div className="size-10 bg-indigo-500 text-white rounded-lg flex items-center justify-center shadow-lg shadow-indigo-500/30">
                            <span className="material-symbols-outlined">auto_fix</span>
                        </div>
                        <div>
                            <h3 className="font-bold text-slate-900 dark:text-white">AI Workflow Creator</h3>
                            <p className="text-xs text-slate-500">Describe what you want, and I'll build the n8n file for you.</p>
                        </div>
                    </div>

                    <div className="space-y-4">
                        <Input
                            label="Describe your automation"
                            placeholder="e.g., When I send a message, translate it to French and save it to a Google Sheet."
                            value={workflowPrompt}
                            onChange={(e) => setWorkflowPrompt(e.target.value)}
                            icon="magic_button"
                        />

                        <Button
                            onClick={handleGenerateWorkflow}
                            className="w-full bg-indigo-600 hover:bg-indigo-700 text-white"
                            isLoading={isGenerating}
                            disabled={!workflowPrompt || isGenerating}
                        >
                            Generate Workflow JSON
                        </Button>
                    </div>

                    {generatedJson && (
                        <div className="space-y-3 animate-in fade-in slide-in-from-bottom-4">
                            <div className="bg-slate-900 text-slate-200 p-4 rounded-xl font-mono text-xs overflow-x-auto max-h-60 custom-scrollbar border border-slate-700">
                                <pre>{JSON.stringify(JSON.parse(generatedJson), null, 2)}</pre>
                            </div>
                            <div className="flex gap-3">
                                <Button
                                    onClick={() => {
                                        const blob = new Blob([generatedJson], { type: 'application/json' });
                                        const url = URL.createObjectURL(blob);
                                        const a = document.createElement('a');
                                        a.href = url;
                                        a.download = 'generated_workflow.json';
                                        a.click();
                                        showToast('Workflow downloaded!', 'success');
                                    }}
                                    className="flex-1 bg-green-600 hover:bg-green-700 text-white"
                                >
                                    <span className="material-symbols-outlined mr-2">download</span>
                                    Download JSON
                                </Button>
                                <Button
                                    onClick={() => {
                                        navigator.clipboard.writeText(generatedJson);
                                        showToast('Copied to clipboard!', 'info');
                                    }}
                                    className="flex-1 bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 text-slate-900 dark:text-white"
                                >
                                    <span className="material-symbols-outlined mr-2">content_copy</span>
                                    Copy Code
                                </Button>
                            </div>
                            <p className="text-[10px] text-center text-slate-500">Import this file into n8n to use logic crafted by Gemini.</p>
                        </div>
                    )}
                </Card>

                <div className="flex justify-end pt-4">
                    <Button onClick={handleSave} size="lg" className="px-8">
                        Save Changes
                    </Button>
                </div>
            </div>
        </div >
    );
};

export default SettingsScreen;
