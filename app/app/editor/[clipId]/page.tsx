"use client";
import React, { useState } from 'react';
import { Sidebar } from '@/components/sidebar';
import { useParams } from 'next/navigation';

export default function ClipEditorPage() {
    const params = useParams();
    const clipId = params.clipId as string;

    return (
        <div className="min-h-screen bg-black text-white">
            <Sidebar />
            <main className="ml-[60px] p-8">
                <h1 className="text-3xl font-bold mb-4">Clip Editor</h1>
                <p className="text-gray-400">Editing clip: {clipId}</p>
                <p className="text-sm text-gray-500 mt-4">Editor coming soon...</p>
            </main>
        </div>
    );
}
