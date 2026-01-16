
import { MdArrowForward } from "react-icons/md";
import "./Styles/map.css"
import { useState } from "react";

export default function Map({ datos, onClick }) {

    const [selectedId, setSelectedId] = useState(null);

    return (
        <div id="Map">
            {datos.map((item, index) => (
                <div className="Map-Item" key={index} onClick={() => [onClick(item), setSelectedId(index)]} style={selectedId === index ? { backgroundColor: "var(--bg-primary)" } : {}}>
                    <div className="Map-Item-Header">
                        <h3 className="Map-Item-Title">{item.payload.Puesto}</h3>
                        <span className="Map-Item-Modalidad">{item.payload.Modalidad}</span>
                    </div>
                    <div className="Map-Item-Details">
                        <div className="Map-Item-Detail">
                            <span className="Detail-Label">Sueldo:</span>
                            <span className="Detail-Value">{item.payload.Sueldo}</span>
                        </div>
                        <div className="Map-Item-Detail">
                            <span className="Detail-Label">Horario:</span>
                            <span className="Detail-Value">{item.payload.Horario}</span>
                        </div>
                        <div className="Map-Item-Detail">
                            <span className="Detail-Label">Ubicación:</span>
                            <span className="Detail-Value">{item.payload.Ubicacion}</span>
                        </div>
                    </div>
                    <div className="Map-Item-Button">
                        <MdArrowForward size={18} />
                    </div>
                </div>
            ))}
        </div>
    );
}
