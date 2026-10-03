import React, { useRef, useLayoutEffect } from "react";
import { PiPaperclipBold } from "react-icons/pi";
import { VscSend } from "react-icons/vsc";
import { CgSpinner } from "react-icons/cg";
import "./Styles/TextInput.css";

export default function TextInput({
  inputText,
  setInputText,
  setSearchButton,
  textinputWidth,
  textinputheight,
  buttonborderradius,
  buttonwidth,
  buttonheight,
  buttonborderradiustopRight,
  textinputContainerWidth,
  borderradius,
  gap,
  hide,
  margin,
  onKeyDown,
  loading = false,
  isLoading = false,
}) {
  const isCargando = Boolean(loading || isLoading || hide);
  const textareaRef = useRef(null);

  // Auto-ajustar altura antes de que el navegador pinte
  useLayoutEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    // 1. Guardar altura actual
    const fromH = textarea.offsetHeight;

    // 2. Medir altura natural del contenido
    textarea.style.transition = "none";
    textarea.style.height = "auto";
    const toH = Math.min(Math.max(textarea.scrollHeight, 40), 180);

    // 3. Si no cambió, fijar y salir
    if (fromH === toH) {
      textarea.style.height = `${toH}px`;
      textarea.style.transition = "";
      return;
    }

    // 4. Fijar en la altura anterior para que el browser pinte desde ahí
    textarea.style.height = `${fromH}px`;
    textarea.offsetHeight; // forzar layout

    // 5. Restaurar transición CSS y animar hacia la nueva altura
    textarea.style.transition = "";
    textarea.style.height = `${toH}px`;
  }, [inputText]);

  const handleInternalKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (setSearchButton) {
        setSearchButton();
      }
    } else if (onKeyDown) {
      onKeyDown(e);
    }
  };

  return (
    <div id="TextInput-Content" style={{ width: textinputContainerWidth, padding: '0px', marginBottom: margin, gap: gap }}>
      {hide ? null : (
        <textarea
          ref={textareaRef}
          id="TextInput"
          rows={1}
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={handleInternalKeyDown}
          placeholder="Escribe el empleo que buscas..."
          style={{
            width: textinputWidth,
            height: textinputheight,
            borderTopLeftRadius: borderradius,
            borderBottomLeftRadius: borderradius,
            borderBottomRightRadius: borderradius,
            borderTopRightRadius: buttonborderradiustopRight,
          }}
        />
      )}
      <div id="Upload-File-Icon" style={{
        borderRadius: buttonborderradius,
        width: buttonwidth,
        height: buttonheight,
      }}>
        {isCargando ? (
          <CgSpinner
            className="spinner-ruedita"
            size={24}
            color="var(--bg-primary, white)"
            title="Cargando..."
          />
        ) : inputText ? (
          <VscSend
            color="var(--bg-primary, white)"
            size={25}
            onClick={setSearchButton}
            style={{ cursor: "pointer" }}
          />
        ) : (
          <PiPaperclipBold color="var(--bg-primary, white)" size={25} />
        )}
      </div>
      {hide ? (
        <div>
          <text>Buscando empleos...</text>
        </div>
      ) : null}
    </div>
  );
}
