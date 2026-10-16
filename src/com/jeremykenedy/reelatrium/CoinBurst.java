package com.jeremykenedy.reelatrium;

import android.opengl.Matrix;
import com.google.android.filament.*;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.FloatBuffer;
import java.nio.ShortBuffer;

/** Shared beveled coin geometry uses up to three bounded instanced draws for a celebration. */
final class CoinBurst {
  private static final int BATCH_SIZE = 64;
  private static final int BATCHES = 3;
  private final Engine engine;
  private final Scene scene;
  private final int[] entities = new int[BATCHES];
  private final VertexBuffer vertices;
  private final IndexBuffer indices;
  private final InstanceBuffer[] instances = new InstanceBuffer[BATCHES];
  private final MaterialInstance material;
  private final float[] transforms = new float[BATCH_SIZE * 16];
  private final boolean[] visible = new boolean[BATCHES];

  CoinBurst(Engine engine, Scene scene, MaterialInstance trim) {
    this.engine = engine;
    this.scene = scene;
    material = MaterialInstance.duplicate(trim, "Gold payout coins");
    material.setParameter("baseColorFactor", .83f, .46f, .065f, 1f);
    material.setParameter("metallicFactor", 1f);
    material.setParameter("roughnessFactor", .22f);
    int segments = 24;
    float[] radius = {0, .034f, .04f, .04f, .034f, 0};
    float[] depth = {.005f, .005f, .0025f, -.0025f, -.005f, -.005f};
    int count = radius.length * (segments + 1);
    FloatBuffer positions = floats(count * 3);
    FloatBuffer normals = floats(count * 3);
    for (int ring = 0; ring < radius.length; ring++) {
      for (int step = 0; step <= segments; step++) {
        float cosine = (float) Math.cos(step * Math.PI * 2 / segments);
        float sine = (float) Math.sin(step * Math.PI * 2 / segments);
        positions.put(radius[ring] * cosine).put(radius[ring] * sine).put(depth[ring]);
        float radial = ring <= 1 || ring >= 4 ? 0 : 1;
        float normalZ = ring <= 1 ? 1 : ring >= 4 ? -1 : 0;
        if (ring == 0) normalZ = 1;
        if (ring == 5) normalZ = -1;
        if (ring == 2 || ring == 3) radial = 1;
        normals.put(radial * cosine).put(radial * sine).put(normalZ);
      }
    }
    positions.flip();
    normals.flip();
    FloatBuffer tangents = floats(count * 4);
    SurfaceOrientation orientation =
        new SurfaceOrientation.Builder().vertexCount(count).normals(normals).build();
    orientation.getQuatsAsFloat(tangents);
    orientation.destroy();
    tangents.rewind();
    vertices =
        new VertexBuffer.Builder()
            .vertexCount(count)
            .bufferCount(3)
            .attribute(VertexBuffer.VertexAttribute.POSITION, 0, VertexBuffer.AttributeType.FLOAT3)
            .attribute(VertexBuffer.VertexAttribute.TANGENTS, 1, VertexBuffer.AttributeType.FLOAT4)
            .attribute(
                VertexBuffer.VertexAttribute.UV0, 2, VertexBuffer.AttributeType.FLOAT2, 0, 32)
            .attribute(
                VertexBuffer.VertexAttribute.UV1, 2, VertexBuffer.AttributeType.FLOAT2, 8, 32)
            .attribute(
                VertexBuffer.VertexAttribute.COLOR, 2, VertexBuffer.AttributeType.FLOAT4, 16, 32)
            .build(engine);
    FloatBuffer attributes = floats(count * 8);
    for (int i = 0; i < count; i++) attributes.put(new float[] {0, 0, 0, 0, 1, 1, 1, 1});
    attributes.flip();
    vertices.setBufferAt(engine, 2, attributes);
    vertices.setBufferAt(engine, 0, positions);
    vertices.setBufferAt(engine, 1, tangents);
    ShortBuffer triangles =
        ByteBuffer.allocateDirect((radius.length - 1) * segments * 6 * 2)
            .order(ByteOrder.nativeOrder())
            .asShortBuffer();
    for (int ring = 0; ring < radius.length - 1; ring++)
      for (int step = 0; step < segments; step++) {
        short a = (short) (ring * (segments + 1) + step);
        short b = (short) (a + 1);
        short c = (short) (a + segments + 1);
        short d = (short) (c + 1);
        triangles.put(a).put(c).put(b).put(b).put(c).put(d);
      }
    triangles.flip();
    indices =
        new IndexBuffer.Builder()
            .indexCount(triangles.remaining())
            .bufferType(IndexBuffer.Builder.IndexType.USHORT)
            .build(engine);
    indices.setBuffer(engine, triangles);
    for (int i = 0; i < BATCH_SIZE; i++) Matrix.setIdentityM(transforms, i * 16);
    // Filament limits automatic local transforms to 64 instances per renderable.
    for (int batch = 0; batch < BATCHES; batch++) {
      entities[batch] = EntityManager.get().create();
      instances[batch] =
          new InstanceBuffer.Builder(BATCH_SIZE).localTransforms(transforms).build(engine);
      new RenderableManager.Builder(1)
          .boundingBox(new Box(0, 1, 1, 4, 4, 4))
          .geometry(0, RenderableManager.PrimitiveType.TRIANGLES, vertices, indices)
          .material(0, material)
          .instances(BATCH_SIZE, instances[batch])
          .culling(false)
          .castShadows(false)
          .receiveShadows(false)
          .build(engine, entities[batch]);
    }
  }

  void update(double age, int count, double duration, long round, boolean fullscreen) {
    boolean active = count > 0 && age >= 0 && age < duration + 2.8;
    for (int batch = 0; batch < BATCHES; batch++) {
      boolean batchActive = active && count > batch * BATCH_SIZE;
      if (batchActive != visible[batch]) {
        if (batchActive) scene.addEntity(entities[batch]);
        else scene.remove(entities[batch]);
        visible[batch] = batchActive;
      }
      if (!batchActive) continue;
      for (int local = 0; local < BATCH_SIZE; local++) {
        int i = batch * BATCH_SIZE + local;
        int offset = local * 16;
        Matrix.setIdentityM(transforms, offset);
        double delay = i * 1.2 / Math.max(1, count - 1);
        double birth = delay + Math.floor(Math.max(0, age - delay) / 1.8) * 1.8;
        double t = age - birth;
        if (i >= count || t < 0 || birth >= duration || t > 2.8) {
          Matrix.scaleM(transforms, offset, 0, 0, 0);
          continue;
        }
        double variation = Math.sin((round + 1) * 73.13 + i * 19.71 + birth * 17.3);
        float x = (float) (variation * t * .8);
        float y = (float) (.42 + (2.35 + .45 * Math.cos(i * 7.1)) * t - 1.85 * t * t);
        float z = (float) (.55 + t * (.50 + .2 * Math.sin(i * 3.7)));
        if (fullscreen) {
          x = x * .9f + (float) variation * .12f;
          y = .74f + (y - .42f) * .55f;
          z = 1.1f;
        }
        Matrix.translateM(transforms, offset, x, y, z);
        if (fullscreen) Matrix.scaleM(transforms, offset, .6f, .6f, .6f);
        Matrix.rotateM(transforms, offset, (float) (t * 430 + i * 41), .7f, 1f, .3f);
      }
      instances[batch].setLocalTransforms(transforms, BATCH_SIZE);
    }
  }

  void destroy() {
    for (int batch = 0; batch < BATCHES; batch++) {
      scene.remove(entities[batch]);
      engine.destroyEntity(entities[batch]);
      EntityManager.get().destroy(entities[batch]);
      engine.destroyInstanceBuffer(instances[batch]);
    }
    engine.destroyVertexBuffer(vertices);
    engine.destroyIndexBuffer(indices);
    engine.destroyMaterialInstance(material);
  }

  private static FloatBuffer floats(int count) {
    return ByteBuffer.allocateDirect(count * 4).order(ByteOrder.nativeOrder()).asFloatBuffer();
  }
}
