import React, { useState, useEffect, useRef } from "react";
import "./Styles/header.css";
import { IoSunnyOutline } from "react-icons/io5";
import { SiRobotframework } from "react-icons/si";
import { HiSun } from "react-icons/hi";
import { useTheme } from "./ThemeContext";
import NavSections from "./Components/NavSections";
import FrameAnimation from "./Components/FrameAnimation";
import video from "../assets/drawing_animation.mp4";
import video2 from "../assets/video2.mp4";
import video3 from "../assets/video3.mp4";

export default function Header() {
  const { mode, toggleMode } = useTheme();
  const [activeSection, setActiveSection] = useState(null);

  const video1Ref = useRef(null);
  const video2Ref = useRef(null);
  const video3Ref = useRef(null);

  const [video2Started, setVideo2Started] = useState(false);
  const [video3Started, setVideo3Started] = useState(false);

  const handleToggleSection = (sectionId) => {
    setActiveSection((prev) => (prev === sectionId ? null : sectionId));
  };

  const isExpanded = Boolean(activeSection);

  useEffect(() => {
    const handleClickOutside = (e) => {
      const headerEl = document.getElementById("Header");
      if (headerEl && !headerEl.contains(e.target)) {
        setActiveSection(null);
      }
    };
    if (isExpanded) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isExpanded]);

  // Control de inicio temporizado para Video 1, Video 2 y Video 3
  useEffect(() => {
    if (!isExpanded) {
      // Al cerrarse el header, pausar y resetear los videos
      if (video1Ref.current) {
        video1Ref.current.pause();
        video1Ref.current.currentTime = 0;
      }
      if (video2Ref.current) {
        video2Ref.current.pause();
        video2Ref.current.currentTime = 0;
      }
      if (video3Ref.current) {
        video3Ref.current.pause();
        video3Ref.current.currentTime = 0;
      }
      setVideo2Started(false);
      setVideo3Started(false);
      return;
    }

    // Video 1 inicia inmediatamente
    if (video1Ref.current) {
      video1Ref.current.currentTime = 0;
      video1Ref.current.play().catch(() => { });
    }

    // Asegurar que Video 2 y 3 comiencen pausados y en el segundo 0
    if (video2Ref.current) {
      video2Ref.current.pause();
      video2Ref.current.currentTime = 0;
    }
    if (video3Ref.current) {
      video3Ref.current.pause();
      video3Ref.current.currentTime = 0;
    }
    setVideo2Started(false);
    setVideo3Started(false);

    // Video 2 se inicia 3 segundos después de haber iniciado Video 1
    const timerVideo2 = setTimeout(() => {
      if (video2Ref.current) {
        video2Ref.current.currentTime = 0;
        video2Ref.current.play().catch(() => { });
      }
      setVideo2Started(true);
    }, 3000);

    // Video 3 se inicia 6 segundos después de Video 2 (3s + 6s = 9 segundos)
    const timerVideo3 = setTimeout(() => {
      if (video3Ref.current) {
        video3Ref.current.currentTime = 0;
        video3Ref.current.play().catch(() => { });
      }
      setVideo3Started(true);
    }, 9000);

    return () => {
      clearTimeout(timerVideo2);
      clearTimeout(timerVideo3);
    };
  }, [isExpanded]);

  return (
    <div id="Header" className={isExpanded ? "expanded" : ""}>
      <div id="Header-Top-Bar">
        <div className="Header-Logo-container">
          <div
            id="Logo"
            onClick={() => {
              setActiveSection(null);
              window.dispatchEvent(new CustomEvent('reset-home-search'));
            }}
            style={{ cursor: "pointer" }}
            title="AUTOEMPLEO"
          >
            <SiRobotframework size={25} color="var(--bg-primary)" />
          </div>
          <div
            id="NombreDePagina"
            onClick={() => {
              setActiveSection(null);
              window.dispatchEvent(new CustomEvent('reset-home-search'));
            }}
            style={{ cursor: "pointer" }}
          >
            AUTOEMPLEO
          </div>
        </div>
        <NavSections
          activeSection={activeSection}
          onSelectSection={handleToggleSection}
        />
        <div id="Modo_claro_oscuro">
          {mode === "dark" ? (
            <HiSun size={25} color="var(--icon-color)" onClick={toggleMode} />
          ) : (
            <IoSunnyOutline
              size={25}
              color="var(--icon-color)"
              onClick={toggleMode}
            />
          )}
        </div>
      </div>
      <div id="Header-Expanded-Content">
        {/* <FrameAnimation isPlaying={isExpanded} fps={31} className="Header-Image" /> */}
        <video
          ref={video1Ref}
          loop
          muted
          playsInline
          id="Video-Header"
        >
          <source src={video2} type="video/mp4" />
        </video>
        <video
          ref={video2Ref}
          loop
          muted
          playsInline
          id="Video-Header2"
          style={{
            opacity: video2Started ? undefined : 0,
            transition: "opacity 0.4s ease",
          }}
        >
          <source src={video} type="video/mp4" />
        </video>
        <video
          ref={video3Ref}
          loop
          muted
          playsInline
          id="Video-Header3"
          style={{
            opacity: video3Started ? undefined : 0,
            transition: "opacity 0.4s ease",
          }}
        >
          <source src={video3} type="video/mp4" />
        </video>
      </div>
    </div>
  );
}
