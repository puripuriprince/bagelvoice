import { useState, useEffect, useRef } from "react";
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
	const [audioExists, setAudioExists] = useState(false);
	const [mediaReady, setMediaReady] = useState(false);
	const videoRef = useRef(null);
	const audioRef = useRef(null);

	// Derive audio URL from video URL by replacing "videos" with "audio"
	const getAudioUrl = videoUrl => {
		if (!videoUrl) return null;
		return videoUrl.replace("/videos/", "/audio/");
	};

	// Check if both media files exist
	useEffect(() => {
		if (message.video) {
			const audioUrl = getAudioUrl(message.video);

			const checkMediaExistence = async () => {
				if (!message.video) return;

				try {
					// Check video
					const videoResponse = await fetch(message.video, {
						method: "HEAD",
					});

					// Check audio
					const audioResponse = await fetch(audioUrl, {
						method: "HEAD",
					});

					setVideoExists(videoResponse.ok);
					setAudioExists(audioResponse.ok);

					// Set mediaReady if both exist
					if (videoResponse.ok && audioResponse.ok) {
						setMediaReady(true);
					}
				} catch (error) {
					console.error("Error checking media:", error);
				}
			};

			const intervalId = setInterval(checkMediaExistence, 5000); // Poll every 5 seconds
			checkMediaExistence(); // Check immediately as well

			// Cleanup interval on component unmount or when media is found
			return () => clearInterval(intervalId);
		}
	}, [message.video]);

	// Create a custom video controls handler to synchronize playback perfectly
	const handleVideoPlay = () => {
		if (videoRef.current && audioRef.current) {
			// Ensure they start at the same time
			audioRef.current.currentTime = videoRef.current.currentTime;

			// Play both together
			const audioPromise = audioRef.current.play();

			// Handle potential autoplay policy issues
			if (audioPromise !== undefined) {
				audioPromise.catch(error => {
					console.error("Audio autoplay failed:", error);
					// If audio fails to play, pause video to keep them in sync
					videoRef.current.pause();
				});
			}
		}
	};

	const handleVideoPause = () => {
		if (audioRef.current) {
			audioRef.current.pause();
		}
	};

	const handleVideoSeeked = () => {
		if (videoRef.current && audioRef.current) {
			audioRef.current.currentTime = videoRef.current.currentTime;

			// If video was playing before seeking, ensure audio resumes
			if (!videoRef.current.paused) {
				audioRef.current.play();
			}
		}
	};

	const handleVideoRateChange = () => {
		if (videoRef.current && audioRef.current) {
			audioRef.current.playbackRate = videoRef.current.playbackRate;
		}
	};

	// Setup event listeners for synchronized playback
	useEffect(() => {
		if (mediaReady && videoRef.current && audioRef.current) {
			// Setup event listeners
			videoRef.current.addEventListener("play", handleVideoPlay);
			videoRef.current.addEventListener("pause", handleVideoPause);
			videoRef.current.addEventListener("seeked", handleVideoSeeked);
			videoRef.current.addEventListener(
				"ratechange",
				handleVideoRateChange,
			);

			// Handle volume separately to keep audio/video volumes independent

			return () => {
				// Clean up event listeners
				if (videoRef.current) {
					videoRef.current.removeEventListener(
						"play",
						handleVideoPlay,
					);
					videoRef.current.removeEventListener(
						"pause",
						handleVideoPause,
					);
					videoRef.current.removeEventListener(
						"seeked",
						handleVideoSeeked,
					);
					videoRef.current.removeEventListener(
						"ratechange",
						handleVideoRateChange,
					);
				}
			};
		}
	}, [mediaReady]);

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

			{message.video && mediaReady && (
				<div className="mt-2 relative">
					<video
						ref={videoRef}
						type="video/mp4"
						src={message.video}
						controls
						className="w-full"
					/>
					<audio
						ref={audioRef}
						src={getAudioUrl(message.video)}
						className="hidden" // Hide the audio element
					/>
				</div>
			)}

			{!mediaReady && message.video && (
				<div className="w-full h-[300px] border rounded-lg bg-neutral-900 p-4 mt-2 font-bold flex items-center justify-center">
					<p>Video/audio are being generated, please wait ...</p>
				</div>
			)}
		</div>
	);
}
