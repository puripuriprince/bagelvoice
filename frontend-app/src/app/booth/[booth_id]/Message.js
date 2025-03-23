import { useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import rehypeSanitize from "rehype-sanitize";
import "katex/dist/katex.min.css";

// Helper function to check if a message might contain incomplete LaTeX
const containsIncompleteLatex = text => {
	if (!text) return false;

	// Check for unmatched $ symbols which might indicate incomplete LaTeX
	const dollarCount = (text.match(/\$/g) || []).length;
	if (dollarCount % 2 !== 0) return true;

	// Check for potentially incomplete LaTeX commands/environments
	const openBraces = (text.match(/\{/g) || []).length;
	const closeBraces = (text.match(/\}/g) || []).length;
	if (openBraces !== closeBraces) return true;

	// Check for incomplete \begin{...} \end{...} pairs
	const beginCount = (text.match(/\\begin\{/g) || []).length;
	const endCount = (text.match(/\\end\{/g) || []).length;
	if (beginCount !== endCount) return true;

	return false;
};

export default function Message({ message }) {
	const [videoExists, setVideoExists] = useState(false);

	useEffect(() => {
		if (message.video) {
			const checkVideoExistence = async () => {
				if (!message.video) return;

				try {
					const response = await fetch(message.video, {
						method: "HEAD",
					});
					if (response.ok) {
						setVideoExists(true);
					} else {
						setVideoExists(false);
					}
				} catch (error) {
					console.error("Error checking video:", error);
					setVideoExists(false);
				}
			};
			const intervalId = setInterval(checkVideoExistence, 5000); // Poll every 5 seconds
			checkVideoExistence(); // Check immediately as well
			// Cleanup interval on component unmount or when video is found
			return () => clearInterval(intervalId);
		}
	}, [message.video]);

	// Function to render message content with Markdown and LaTeX support
	const renderMessageContent = () => {
		// If message is potentially streaming and has incomplete LaTeX, render as plain text
		if (message.isStreaming && containsIncompleteLatex(message.message)) {
			return (
				<p className="mt-2 whitespace-pre-wrap">{message.message}</p>
			);
		}

		return (
			<div className="mt-2 markdown-content">
				<ReactMarkdown
					key={message.message}
					remarkPlugins={[remarkMath]}
					rehypePlugins={[rehypeKatex, rehypeSanitize]}
				>
					{message.message || ""}
				</ReactMarkdown>
			</div>
		);
	};

	console.log(message.video, "IS VIDEO");
	return (
		<div className="p-4" key={message.id}>
			<div className="flex gap-4 items-center">
				{message.user !== "Me" && (
					<img className="rounded-full w-12 h-12 bg-white" />
				)}
				<h2
					className={`font-bold ${message.user === "Me" && "text-green-400"}`}
				>
					{message.user}
					{message.isStreaming && (
						<span className="text-xs ms-2 text-yellow-400">
							(typing...)
						</span>
					)}
				</h2>
			</div>

			{renderMessageContent()}
			{message.video && videoExists && (
				<video
					type="video/mp4"
					src={message.video}
					controls
					autoPlay
					className="w-full mt-2"
				/>
			)}
			{!videoExists && message.video && (
				<div className="w-full h-[300px] border rounded-lg bg-neutral-900 p-4 mt-2 font-bold flex items-center justify-center">
					<p>A video is being processed, please wait ...</p>
				</div>
			)}
		</div>
	);
}
