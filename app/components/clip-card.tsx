import React from 'react';
import { Play, Download, Share2, Scissors } from 'lucide-react';
import { Button } from './ui/button';
import { cn } from '@/lib/utils';

type ClipProps = {
    title: string;
    duration: string;
    score: number;
    reasoning?: string;
    thumbnailUrl?: string; // Placeholder for now
};

export function ClipCard({ title, duration, score, reasoning }: ClipProps) {
    // Determine color based on score
    const scoreColor = score >= 85 ? "bg-score-high" : score >= 70 ? "bg-score-mid" : "bg-score-low";

    return (
        <div className="group relative bg-surface border border-border rounded-xl overflow-hidden hover:border-primary-gradient_start transition-all duration-300">
            <div className="flex flex-col md:flex-row gap-4 p-4">
                {/* Thumbnail / Video Placeholder */}
                <div className="relative w-full md:w-32 aspect-[9/16] bg-black rounded-lg overflow-hidden shrink-0 group-hover:shadow-[0_0_15px_rgba(143,0,255,0.2)] transition-shadow">
                    <div className="absolute inset-0 flex items-center justify-center">
                        <Play className="w-8 h-8 text-white opacity-50 group-hover:opacity-100 transition-opacity fill-current" />
                    </div>
                    {/* Duration Badge */}
                    <div className="absolute bottom-1 right-1 bg-black/80 px-1.5 py-0.5 rounded text-[10px] font-mono text-white">
                        {duration}
                    </div>
                </div>

                {/* Content */}
                <div className="flex-1 space-y-2">
                    <div className="flex items-start justify-between">
                        <h3 className="font-semibold text-lg text-white leading-tight line-clamp-2 pr-12">
                            {title}
                        </h3>
                        {/* Viral Score Badge */}
                        <div className="absolute top-4 right-4 flex flex-col items-center">
                            <div className={cn("w-10 h-10 rounded-full flex items-center justify-center font-bold text-black border-2 border-surface shadow-lg", scoreColor)}>
                                {score}
                            </div>
                            <span className="text-[10px] text-text-muted mt-1 font-medium uppercase tracking-wider">Viral</span>
                        </div>
                    </div>

                    <div className="bg-background/50 p-2 rounded text-xs text-text-muted line-clamp-2 border border-border/50">
                        {reasoning || "High engagement potential detected due to strong opening hook."}
                    </div>

                    {/* Action Toolbar */}
                    <div className="flex items-center gap-2 pt-2">
                        <Button size="sm" variant="outline" className="h-8 text-xs gap-1">
                            <Scissors className="w-3 h-3" /> Edit
                        </Button>
                        <Button size="sm" variant="ghost" className="h-8 w-8 p-0">
                            <Download className="w-4 h-4" />
                        </Button>
                        <Button size="sm" variant="ghost" className="h-8 w-8 p-0">
                            <Share2 className="w-4 h-4" />
                        </Button>
                    </div>
                </div>
            </div>
        </div>
    );
}
