package com.jeremykenedy.reelatrium;

import com.google.android.filament.Engine;
import com.google.android.filament.Material;
import com.google.android.filament.MaterialInstance;
import com.google.android.filament.RenderableManager;
import com.google.android.filament.gltfio.FilamentAsset;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.Map;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

/** Uses a compiled solid-surface material for meshes that have no texture inputs. */
final class SolidMaterials {
  private final Engine engine;
  private final Material material;
  private final JSONObject surfaces;
  private final Map<String, MaterialInstance> instances = new LinkedHashMap<>();

  SolidMaterials(Engine engine, ByteBuffer compiled, ByteBuffer descriptions) {
    this.engine = engine;
    material = new Material.Builder().payload(compiled, compiled.remaining()).build(engine);
    byte[] json = new byte[descriptions.remaining()];
    descriptions.get(json);
    try {
      surfaces = new JSONObject(new String(json, StandardCharsets.UTF_8));
    } catch (JSONException error) {
      throw new IllegalStateException("Invalid solid surface descriptions", error);
    }
  }

  MaterialInstance[] apply(FilamentAsset asset) {
    RenderableManager renderables = engine.getRenderableManager();
    for (int entity : asset.getRenderableEntities()) {
      int instance = renderables.getInstance(entity);
      for (int primitive = 0; primitive < renderables.getPrimitiveCount(instance); primitive++) {
        MaterialInstance source = renderables.getMaterialInstanceAt(instance, primitive);
        if (surfaces.has(source.getName()))
          renderables.setMaterialInstanceAt(instance, primitive, replacement(source.getName()));
      }
    }
    MaterialInstance[] result = asset.getInstance().getMaterialInstances();
    for (int i = 0; i < result.length; i++) {
      MaterialInstance replacement = instances.get(result[i].getName());
      if (replacement != null) result[i] = replacement;
    }
    return result;
  }

  private MaterialInstance replacement(String name) {
    MaterialInstance existing = instances.get(name);
    if (existing != null) return existing;
    try {
      JSONObject surface = surfaces.getJSONObject(name);
      MaterialInstance instance = material.createInstance(name);
      JSONArray color = surface.getJSONArray("color");
      instance.setParameter(
          "baseColorFactor",
          (float) color.getDouble(0),
          (float) color.getDouble(1),
          (float) color.getDouble(2),
          (float) color.getDouble(3));
      instance.setParameter("metallicFactor", (float) surface.getDouble("metal"));
      instance.setParameter("roughnessFactor", (float) surface.getDouble("roughness"));
      JSONArray emission = surface.getJSONArray("emission");
      instance.setParameter(
          "emissiveFactor",
          (float) emission.getDouble(0),
          (float) emission.getDouble(1),
          (float) emission.getDouble(2));
      instances.put(name, instance);
      return instance;
    } catch (JSONException error) {
      throw new IllegalStateException("Invalid solid surface: " + name, error);
    }
  }

  void clear() {
    for (MaterialInstance instance : instances.values()) engine.destroyMaterialInstance(instance);
    instances.clear();
  }

  void destroy() {
    clear();
    engine.destroyMaterial(material);
  }
}
