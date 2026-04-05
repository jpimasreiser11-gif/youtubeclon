import Link from 'next/link';

export default function NotFound() {
    return (
        <div className="min-h-screen bg-black flex items-center justify-center">
            <div className="text-center">
                <h1 className="text-6xl font-bold text-orange-500 mb-4">404</h1>
                <h2 className="text-2xl font-semibold text-white mb-4">Página no encontrada</h2>
                <p className="text-gray-400 mb-8">La página que buscas no existe</p>
                <Link
                    href="/dashboard"
                    className="bg-orange-600 hover:bg-orange-700 text-white px-6 py-3 rounded-lg font-semibold transition"
                >
                    Ir al Dashboard
                </Link>
            </div>
        </div>
    );
}
