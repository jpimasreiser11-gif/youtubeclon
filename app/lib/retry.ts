import logger from './logger';

export interface RetryOptions {
    maxRetries?: number;
    baseDelay?: number;
    maxDelay?: number;
    onRetry?: (attempt: number, error: Error) => void;
}

/**
 * Retry a function with exponential backoff
 * @param fn Function to retry
 * @param options Retry configuration
 * @returns Promise with the function result
 */
export async function retryWithBackoff<T>(
    fn: () => Promise<T>,
    options: RetryOptions = {}
): Promise<T> {
    const {
        maxRetries = 3,
        baseDelay = 1000,
        maxDelay = 10000,
        onRetry
    } = options;

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
            return await fn();
        } catch (error) {
            const isLastAttempt = attempt === maxRetries;

            if (isLastAttempt) {
                throw error;
            }

            // Calculate exponential backoff delay
            const delay = Math.min(baseDelay * Math.pow(2, attempt - 1), maxDelay);

            // Call onRetry callback if provided
            if (onRetry) {
                onRetry(attempt, error as Error);
            }

            logger.warn(`Retry attempt ${attempt}/${maxRetries} after ${delay}ms`, {
                error: (error as Error).message,
                attempt,
                delay
            });

            // Wait before retrying
            await sleep(delay);
        }
    }

    throw new Error('Retry failed - should not reach here');
}

/**
 * Helper function to sleep for a given duration
 */
export function sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Retry specifically for fetch requests with better error handling
 */
export async function retryFetch(
    url: string,
    options?: RequestInit,
    retryOptions?: RetryOptions
): Promise<Response> {
    return retryWithBackoff(
        async () => {
            const response = await fetch(url, options);

            // Retry on 5xx errors
            if (response.status >= 500) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            // Don't retry on 4xx errors (client errors)
            if (response.status >= 400 && response.status < 500) {
                logger.error('Client error, not retrying', {
                    status: response.status,
                    url
                });
            }

            return response;
        },
        retryOptions
    );
}

/**
 * Wrapper for exec commands with retry
 */
export async function retryExec(
    execFn: () => Promise<{ stdout: string; stderr: string }>,
    retryOptions?: RetryOptions
): Promise<{ stdout: string; stderr: string }> {
    return retryWithBackoff(execFn, {
        ...retryOptions,
        onRetry: (attempt, error) => {
            logger.warn('Retrying exec command', {
                attempt,
                error: error.message
            });
            if (retryOptions?.onRetry) {
                retryOptions.onRetry(attempt, error);
            }
        }
    });
}
