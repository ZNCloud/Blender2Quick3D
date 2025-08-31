import QtQuick
import QtQuick3D

Node {
    id: node

    // Resources
    property url textureData: "maps/textureData.png"
    Texture {
        id: _0_texture
        generateMipmaps: true
        mipFilter: Texture.Linear
        source: node.textureData
    }
    PrincipledMaterial {
        id: material_001_material
        objectName: "Material.001"
        baseColorMap: _0_texture
        roughness: 0.3417721390724182
        cullMode: PrincipledMaterial.NoCulling
        alphaMode: PrincipledMaterial.Opaque
    }

    // Nodes:
    Node {
        id: root
        objectName: "ROOT"
        Model {
            id: cube
            objectName: "Cube"
            source: "meshes/cube_mesh.mesh"
            materials: [
                material_001_material
            ]
        }
        DirectionalLight {
            id: light_light
            objectName: "Light"
            position: Qt.vector3d(4.07625, 5.90386, -1.00545)
            rotation: Qt.quaternion(0.523275, -0.284166, 0.726942, 0.342034)
            scale: Qt.vector3d(1, 1, 1)
        }
        PerspectiveCamera {
            id: camera_camera
            objectName: "Camera"
            position: Qt.vector3d(-18.0243, 22.4046, 48.5709)
            rotation: Qt.quaternion(0.955938, -0.166613, -0.238119, -0.0415032)
            clipNear: 0.10000000149011612
            clipFar: 100
            fieldOfView: 39.59775924682617
            fieldOfViewOrientation: PerspectiveCamera.Horizontal
        }
        Model {
            id: suzanne
            objectName: "Suzanne"
            position: Qt.vector3d(-2.03065, 4.99219, -1.55641)
            scale: Qt.vector3d(3.98025, 3.98025, 3.98025)
            source: "meshes/suzanne_mesh.mesh"
            materials: [
                material_001_material
            ]
        }
        Model {
            id: suzanne_001
            objectName: "Suzanne.001"
            position: Qt.vector3d(10.7944, 0.552246, 0.182327)
            rotation: Qt.quaternion(0.52446, -0.562184, -0.365298, -0.524832)
            scale: Qt.vector3d(9.61247, 9.61247, 9.61247)
            source: "meshes/mesh_mesh.mesh"
            materials: [
                material_001_material
            ]
        }
    }

    // Animations:
}
